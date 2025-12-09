import json
import os
from translator import translate_segments

# Mock data with IFRS terms and numbers
test_data = {
    "paragraphs": [
        {
            "id": "p1",
            "text": "当期純利益は1,000,000円であった。",
            "comments": []
        },
        {
            "id": "p2",
            "text": "営業利益は▲500,000円となり、減損損失を計上した。",
            "comments": []
        }
    ]
}

print("Running verification...")
try:
    result = translate_segments(test_data)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Translation failure (None returned)")
except Exception as e:
    print(f"Verification script failed: {e}")
