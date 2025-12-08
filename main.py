import argparse
import json
import os
import sys
from parser import parse_document
from translator import translate_segments

def main():
    parser = argparse.ArgumentParser(description="Parse and Translate Word Doc via Gemini")
    parser.add_argument("docx_file", help="Path to the .docx file")
    parser.add_argument("--output", help="Output JSON file path", default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.docx_file):
        print(f"Error: File not found {args.docx_file}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Parsing {args.docx_file}...", file=sys.stderr)
    try:
        parsed_data = parse_document(args.docx_file)
    except Exception as e:
        print(f"Parsing failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("Parsing complete. Sending to Gemini for translation...", file=sys.stderr)
    try:
        translated_data = translate_segments(parsed_data)
        if not translated_data:
            print("Translation failed or returned invalid format.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Translation failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    output_json = json.dumps(translated_data, indent=2, ensure_ascii=False)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

if __name__ == "__main__":
    main()
