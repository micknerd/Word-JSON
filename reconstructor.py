import json
import os
import random
import shutil
import string
import tempfile
import zipfile
from lxml import etree

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
COMMENTS_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"

def generate_id():
    return "".join(random.choices(string.digits, k=5))

def ensure_comments_part(temp_dir):
    """
    Ensures comments.xml exists and is referenced from document rels and content types.
    Returns tuple (comments_tree, comments_root, existing_comment_ids).
    """
    comments_xml_path = os.path.join(temp_dir, 'word', 'comments.xml')
    doc_rels_path = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
    content_types_path = os.path.join(temp_dir, '[Content_Types].xml')

    existing_comment_ids = set()

    # Load or create comments.xml
    if os.path.exists(comments_xml_path):
        comments_tree = etree.parse(comments_xml_path)
        comments_root = comments_tree.getroot()
        for c in comments_root.xpath('//w:comment', namespaces=NAMESPACES):
            existing_comment_ids.add(c.get(f"{{{NAMESPACES['w']}}}id"))
    else:
        comments_root = etree.Element(f"{{{NAMESPACES['w']}}}comments", nsmap=NAMESPACES)
        comments_tree = etree.ElementTree(comments_root)
        os.makedirs(os.path.dirname(comments_xml_path), exist_ok=True)

    # Ensure relationship from document.xml to comments.xml
    os.makedirs(os.path.dirname(doc_rels_path), exist_ok=True)
    if os.path.exists(doc_rels_path):
        rels_tree = etree.parse(doc_rels_path)
        rels_root = rels_tree.getroot()
    else:
        rels_root = etree.Element("Relationships", nsmap={None: REL_NS})
        rels_tree = etree.ElementTree(rels_root)

    existing_rel = rels_root.xpath(f"./rels:Relationship[@Type='{COMMENTS_REL_TYPE}']",
                                   namespaces={'rels': REL_NS})
    if existing_rel:
        rel_id = existing_rel[0].get("Id")
    else:
        # Generate unique rId
        used_ids = {r.get("Id") for r in rels_root.xpath("./rels:Relationship", namespaces={'rels': REL_NS})}
        idx = 1000
        rel_id = f"rId{idx}"
        while rel_id in used_ids:
            idx += 1
            rel_id = f"rId{idx}"
        rel_el = etree.SubElement(rels_root, "Relationship")
        rel_el.set("Id", rel_id)
        rel_el.set("Type", COMMENTS_REL_TYPE)
        rel_el.set("Target", "comments.xml")

    rels_tree.write(doc_rels_path, encoding='UTF-8', xml_declaration=True, standalone="yes")

    # Ensure [Content_Types].xml override for comments
    if os.path.exists(content_types_path):
        ct_tree = etree.parse(content_types_path)
        ct_root = ct_tree.getroot()
    else:
        ct_root = etree.Element("Types", nsmap=None)
        ct_root.set("xmlns", "http://schemas.openxmlformats.org/package/2006/content-types")
        ct_tree = etree.ElementTree(ct_root)

    ct_ns = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
    override_xpath = "./ct:Override[@PartName='/word/comments.xml']"
    if not ct_root.xpath(override_xpath, namespaces=ct_ns):
        override = etree.SubElement(ct_root, "Override")
        override.set("PartName", "/word/comments.xml")
        override.set("ContentType", COMMENTS_CONTENT_TYPE)

    ct_tree.write(content_types_path, encoding='UTF-8', xml_declaration=True, standalone="yes")

    return comments_tree, comments_root, existing_comment_ids

def apply_text_to_runs(paragraph, new_text, color_val=None):
    """
    Replace paragraph text while preserving run structure/styling where possible.
    Splits the new text evenly across existing text nodes; attaches color if provided.
    """
    text_nodes = paragraph.xpath('.//w:t', namespaces=NAMESPACES)
    if not text_nodes:
        return

    total_nodes = len(text_nodes)
    base = len(new_text) // total_nodes
    extra = len(new_text) % total_nodes
    pos = 0

    for idx, t_node in enumerate(text_nodes):
        take = base + (1 if idx < extra else 0)
        segment = new_text[pos:pos + take]
        pos += take
        t_node.text = segment

        parent_run = t_node.getparent()
        if parent_run is not None and color_val:
            rPr = parent_run.find(f"{{{NAMESPACES['w']}}}rPr")
            if rPr is None:
                rPr = etree.Element(f"{{{NAMESPACES['w']}}}rPr", nsmap=NAMESPACES)
                parent_run.insert(0, rPr)
            color_tag = rPr.find(f"{{{NAMESPACES['w']}}}color")
            if color_tag is None:
                color_tag = etree.Element(f"{{{NAMESPACES['w']}}}color", nsmap=NAMESPACES)
                rPr.append(color_tag)
            color_tag.set(f"{{{NAMESPACES['w']}}}val", color_val)

    # If there is remaining text (happens when new_text longer than splits), append a new run
    if pos < len(new_text):
        remaining = new_text[pos:]
        new_run = etree.Element(f"{{{NAMESPACES['w']}}}r", nsmap=NAMESPACES)
        if color_val:
            rPr = etree.SubElement(new_run, f"{{{NAMESPACES['w']}}}rPr", nsmap=NAMESPACES)
            color_tag = etree.SubElement(rPr, f"{{{NAMESPACES['w']}}}color", nsmap=NAMESPACES)
            color_tag.set(f"{{{NAMESPACES['w']}}}val", color_val)
        new_t = etree.SubElement(new_run, f"{{{NAMESPACES['w']}}}t", nsmap=NAMESPACES)
        new_t.text = remaining
        paragraph.append(new_run)

def reconstruct_docx(original_docx_path, translated_json_path, output_docx_path):
    """
    Creates a new docx by replacing text with translations, applying red color for alerts,
    and inserting comments for AI notes.
    """
    
    with open(translated_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Map para_id to data
    trans_map = {p["id"]: p for p in data.get("paragraphs", [])}

    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip
        with zipfile.ZipFile(original_docx_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        doc_xml_path = os.path.join(temp_dir, 'word', 'document.xml')
        comments_xml_path = os.path.join(temp_dir, 'word', 'comments.xml')
        
        # 1. Update comments.xml if ai_generated_comments exist
        comments_tree, comments_root, existing_comment_ids = ensure_comments_part(temp_dir)

        # 2. Process Paragraphs
        doc_tree = etree.parse(doc_xml_path)
        doc_root = doc_tree.getroot()
        paras = doc_root.xpath('//w:p', namespaces=NAMESPACES)
        
        for i, p in enumerate(paras):
            para_id = f"para_{i:03d}"
            if para_id not in trans_map:
                continue
                
            item = trans_map[para_id]
            new_text = item.get("translated_text", "")
            ai_comments = item.get("ai_generated_comments", [])
            
            if not new_text:
                continue

            # Check if we need Red Text (if comments exist, we assume it's "alert" worthy per specs)
            # or if text has specific markers. The user asked for "confidence" -> red.
            # We'll treat presence of AI comments as a trigger for Red Text for now, or just default black.
            # User said: "疑わしい・翻訳に自信のない箇所は赤字" -> implementation detail: 
            # if `ai_generated_comments` is not empty, we assume there's a warning.
            
            is_warning = len(ai_comments) > 0
            color_val = "FF0000" if is_warning else None

            # --- Text Replacement Strategy ---
            # Simplified: Clear all runs, add a new single run with the text.
            # Complex: Try to preserve bold/italic. For prototype, we replace the first run text 
            # and color it if needed, remove others.
            
            text_nodes = p.xpath('.//w:t', namespaces=NAMESPACES)
            if not text_nodes:
                continue # Skip empty paragraphs
                
            apply_text_to_runs(p, new_text, color_val=color_val)

            # --- Insert Comments ---
            if ai_comments:
                for comment_text in ai_comments:
                    c_id = generate_id()
                    while c_id in existing_comment_ids:
                        c_id = generate_id()
                    existing_comment_ids.add(c_id)
                    
                    # Add to comments.xml
                    # <w:comment w:id="X" ...> ... <w:t>Text</w:t> ... </w:comment>
                    new_comment = etree.Element(f"{{{NAMESPACES['w']}}}comment", nsmap=NAMESPACES)
                    new_comment.set(f"{{{NAMESPACES['w']}}}id", c_id)
                    # Add standard date/author attributes if needed, keep simple for now
                    
                    c_p = etree.SubElement(new_comment, f"{{{NAMESPACES['w']}}}p", nsmap=NAMESPACES)
                    c_r = etree.SubElement(c_p, f"{{{NAMESPACES['w']}}}r", nsmap=NAMESPACES)
                    c_t = etree.SubElement(c_r, f"{{{NAMESPACES['w']}}}t", nsmap=NAMESPACES)
                    c_t.text = f"[AI] {comment_text}"
                    
                    comments_root.append(new_comment)
                    
                    # Link in document.xml
                    # Need <w:commentRangeStart>, <w:commentRangeEnd>, <w:commentReference>
                    # This is tricky without messing up XML.
                    # Safest: Insert <w:commentReference> in the run we modified.
                    
                    # Create reference node
                    # <w:r><w:commentReference w:id="X"/></w:r> 
                    # We append this run to the paragraph
                    ref_run = etree.Element(f"{{{NAMESPACES['w']}}}r", nsmap=NAMESPACES)
                    ref_node = etree.Element(f"{{{NAMESPACES['w']}}}commentReference", nsmap=NAMESPACES)
                    ref_node.set(f"{{{NAMESPACES['w']}}}id", c_id)
                    ref_run.append(ref_node)
                    
                    p.append(ref_run)

        # Write back XMLs
        if comments_root is not None:
            comments_tree.write(comments_xml_path, encoding='UTF-8', xml_declaration=True, standalone="yes")
        
        doc_tree.write(doc_xml_path, encoding='UTF-8', xml_declaration=True, standalone="yes")

        # Zip up
        with zipfile.ZipFile(output_docx_path, 'w', zipfile.ZIP_DEFLATED) as docx_out:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, temp_dir)
                    docx_out.write(file_path, arcname)

    print(f"Refined document saved to {output_docx_path}")

if __name__ == "__main__":
    import sys
    # python reconstructor.py input.docx translation.json output.docx
    reconstruct_docx(sys.argv[1], sys.argv[2], sys.argv[3])
