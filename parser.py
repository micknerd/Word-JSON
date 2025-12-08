import zipfile
from lxml import etree
import json
import os
import sys

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
    """Parses comments.xml and returns a dict mapping comment ID to detail."""
    comments_map = {}
    root = get_xml_tree(docx_path, 'word/comments.xml')
    
    if root is None:
        return comments_map

    for comment in root.xpath('//w:comment', namespaces=NAMESPACES):
        comment_id = comment.get(f"{{{NAMESPACES['w']}}}id")
        author = comment.get(f"{{{NAMESPACES['w']}}}author")
        
        # Extract text parts
        text_parts = comment.xpath('.//w:t/text()', namespaces=NAMESPACES)
        body = "".join(text_parts)
        
        if comment_id:
            comments_map[comment_id] = {
                "id": comment_id,
                "author": author,
                "body": body
            }
            
    return comments_map

def parse_document(docx_path):
    """Parses document.xml for paragraphs, comments, and track changes."""
    paragraphs_data = []
    comments_map = parse_comments(docx_path)
    
    root = get_xml_tree(docx_path, 'word/document.xml')
    if root is None:
        raise ValueError("Could not find word/document.xml in the file")

    paras = root.xpath('//w:p', namespaces=NAMESPACES)
    
    for i, p in enumerate(paras):
        # 1. Extract plain text (including text inside inserts, generally document.xml plain text view)
        # Note: getting text from w:t directly captures current state (after inserts, before deletes usually?)
        # Detailed revision handling (w:ins/w:del) needs careful traversal.
        
        # Simple extraction for "text" field: contents of all w:t
        # This includes added text (w:ins/w:r/w:t) but might exclude deleted text depending on how Word saves it.
        # Usually w:del contains w:delText which is not in w:t.
        text_parts = p.xpath('.//w:t/text()', namespaces=NAMESPACES)
        para_text = "".join(text_parts)
        
        # 2. Revisions (Track Changes)
        # Look for w:ins and w:del
        revisions = []
        
        # Insertions
        inserts = p.xpath('.//w:ins', namespaces=NAMESPACES)
        for ins in inserts:
            ins_id = ins.get(f"{{{NAMESPACES['w']}}}id")
            author = ins.get(f"{{{NAMESPACES['w']}}}author")
            # Text inside insert
            ins_text = "".join(ins.xpath('.//w:t/text()', namespaces=NAMESPACES))
            revisions.append({
                "type": "insert",
                "author": author,
                "text": ins_text,
                "id": ins_id
            })
            
        # Deletions
        deletes = p.xpath('.//w:del', namespaces=NAMESPACES)
        for dl in deletes:
            dl_id = dl.get(f"{{{NAMESPACES['w']}}}id")
            author = dl.get(f"{{{NAMESPACES['w']}}}author")
            # Text inside delete (usually w:delText)
            del_text = "".join(dl.xpath('.//w:delText/text()', namespaces=NAMESPACES))
            revisions.append({
                "type": "delete",
                "author": author,
                "text": del_text,
                "id": dl_id
            })
            
        # 3. Comments
        # We look for comment references: <w:commentReference w:id="X"/>
        comment_refs = p.xpath('.//w:commentReference', namespaces=NAMESPACES)
        current_para_comments = []
        seen_comment_ids = set()
        
        for ref in comment_refs:
            c_id = ref.get(f"{{{NAMESPACES['w']}}}id")
            if c_id and c_id in comments_map and c_id not in seen_comment_ids:
                current_para_comments.append(comments_map[c_id])
                seen_comment_ids.add(c_id)

        # Build paragraph object
        if para_text.strip() or revisions or current_para_comments:
            para_obj = {
                "id": f"para_{i:03d}",
                "text": para_text,
                "comments": current_para_comments,
                "revisions": revisions
            }
            paragraphs_data.append(para_obj)

    return {"paragraphs": paragraphs_data}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_docx>")
        sys.exit(1)
    
    docx_file = sys.argv[1]
    if not os.path.exists(docx_file):
        print(f"Error: File not found: {docx_file}")
        sys.exit(1)
        
    try:
        data = parse_document(docx_file)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error parsing document: {e}", file=sys.stderr)
        sys.exit(1)
