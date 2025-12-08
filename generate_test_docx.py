import zipfile
import os

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:lang w:val="en-US"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>"""

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:t>This is a standard paragraph.</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>This paragraph has a comment.</w:t></w:r>
      <w:commentRangeStart w:id="0"/>
      <w:r><w:t>Check this.</w:t></w:r>
      <w:commentRangeEnd w:id="0"/>
      <w:r>
        <w:commentReference w:id="0"/>
      </w:r>
    </w:p>
    <w:p>
      <w:r><w:t>This line has </w:t></w:r>
      <w:ins w:id="1" w:author="Author1" w:date="2023-01-01T10:00:00Z">
        <w:r><w:t>inserted</w:t></w:r>
      </w:ins>
      <w:del w:id="2" w:author="Author2" w:date="2023-01-01T10:00:00Z">
        <w:r><w:delText>deleted</w:delText></w:r>
      </w:del>
      <w:r><w:t> text.</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""

COMMENTS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:comment w:id="0" w:author="TestAuthor" w:date="2023-01-01T10:00:00Z" w:initials="TA">
    <w:p><w:r><w:t>This is a test comment.</w:t></w:r></w:p>
  </w:comment>
</w:comments>"""

def generate_test_docx(filename):
    with zipfile.ZipFile(filename, 'w') as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES)
        z.writestr('_rels/.rels', RELS)
        z.writestr('word/_rels/document.xml.rels', DOC_RELS)
        z.writestr('word/document.xml', DOCUMENT)
        z.writestr('word/styles.xml', STYLES)
        z.writestr('word/comments.xml', COMMENTS)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_test_docx("test_sample.docx")
