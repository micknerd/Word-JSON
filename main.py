import argparse
import json
import os
import sys
from parser import parse_document
from translator import translate_segments
from reconstructor import reconstruct_docx

def main():
    parser = argparse.ArgumentParser(description="IFRS Document Translation System (Bedrock)")
    parser.add_argument("docx_file", help="Path to the original .docx file")
    parser.add_argument("--output_json", help="Path to save intermediate translated JSON", default="translation_result.json")
    parser.add_argument("--output_docx", help="Path to save final translated .docx", default="translated_output.docx")
    parser.add_argument("--glossary", help="Path to glossary JSON", default=None)
    parser.add_argument("--context", help="Path to context JSON", default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.docx_file):
        print(f"Error: File not found {args.docx_file}", file=sys.stderr)
        sys.exit(1)

    # 1. Parse
    print(f"Parsing {args.docx_file}...", file=sys.stderr)
    try:
        parsed_data = parse_document(args.docx_file)
    except Exception as e:
        print(f"Parsing failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Load Glossary/Context if provided
    glossary = {}
    if args.glossary and os.path.exists(args.glossary):
        with open(args.glossary, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
            
    context_info = {}
    if args.context and os.path.exists(args.context):
        with open(args.context, 'r', encoding='utf-8') as f:
            context_info = json.load(f)

    # 2. Translate (Bedrock)
    print("Sending to AWS Bedrock (Claude 3) for translation...", file=sys.stderr)
    try:
        translated_data = translate_segments(parsed_data, glossary=glossary, context_info=context_info)
        if not translated_data:
            print("Translation returned no data.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Translation failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Save JSON
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, indent=2, ensure_ascii=False)
    print(f"Intermediate JSON saved to {args.output_json}", file=sys.stderr)
    
    # 3. Reconstruct
    print("Reconstructing Word document...", file=sys.stderr)
    try:
        reconstruct_docx(args.docx_file, args.output_json, args.output_docx)
    except Exception as e:
        print(f"Reconstruction failed: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Done! Translated document saved to {args.output_docx}", file=sys.stderr)

if __name__ == "__main__":
    main()
