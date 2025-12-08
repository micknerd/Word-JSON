import zipfile
from lxml import etree
import json
import os

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

def get_xml_tree(docx_path, filename):
    """Extracts XML from the docx (zip) file."""
    with zipfile.ZipFile(docx_path) as z:
        if filename in z.namelist():
            xml_content = z.read(filename)
            return etree.fromstring(xml_content)
    return None

def parse_comments(docx_path):
    """Parses comments.xml and returns a dict mapping comment ID to text."""
    comments_map = {}
    root = get_xml_tree(docx_path, 'word/comments.xml')
    
    if root is None:
        return comments_map

    for comment in root.xpath('//w:comment', namespaces=NAMESPACES):
        comment_id = comment.get(f"{{{NAMESPACES['w']}}}id")
        # Extract all text within the comment
        text_parts = comment.xpath('.//w:t/text()', namespaces=NAMESPACES)
        comment_text = "".join(text_parts)
        if comment_id:
            comments_map[comment_id] = comment_text
            
    return comments_map

def parse_document(docx_path):
    """Parses document.xml and links paragraphs to comments."""
    segments = []
    comments_map = parse_comments(docx_path)
    
    root = get_xml_tree(docx_path, 'word/document.xml')
    if root is None:
        raise ValueError("Could not find word/document.xml in the file")

    paras = root.xpath('//w:p', namespaces=NAMESPACES)
    
    for i, p in enumerate(paras):
        # Extract text
        text_parts = p.xpath('.//w:t/text()', namespaces=NAMESPACES)
        original_text = "".join(text_parts)
        
        if not original_text.strip():
            continue

        # Look for comment references in this paragraph
        # Structure: <w:r><w:commentReference w:id="1"/></w:r>
        # Note: This assigns the comment to the whole paragraph if found within it.
        # Precise range mapping (w:commentRangeStart/End) is harder and might span paras.
        # For this prototype, we associate references found in the para with the para.
        comment_refs = p.xpath('.//w:commentReference', namespaces=NAMESPACES)
        
        associated_comments = []
        seen_ids = set()
        for ref in comment_refs:
            c_id = ref.get(f"{{{NAMESPACES['w']}}}id")
            if c_id and c_id in comments_map and c_id not in seen_ids:
                associated_comments.append({
                    "id": c_id,
                    "text": comments_map[c_id]
                })
                seen_ids.add(c_id)
        
        segment = {
            "id": f"para_{i:03d}",
            "original_text": original_text,
            "associated_comments": associated_comments
        }
        segments.append(segment)

    return {"segments": segments}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python docx_parser.py <path_to_docx>")
        sys.exit(1)
    
    docx_file = sys.argv[1]
    if not os.path.exists(docx_file):
        print(f"File not found: {docx_file}")
        sys.exit(1)
        
    data = parse_document(docx_file)
    print(json.dumps(data, indent=2, ensure_ascii=False))
