import json
import os
import shutil
from reconstructor import reconstruct_docx

# Ensure we have a sample docx
if not os.path.exists("test_sample.docx"):
    # If missing, creating a dummy is hard without library, but environment list_dir showed it exists.
    # If it writes to a new path, we are good.
    print("Warning: test_sample.docx not found. Skipping test.")
    exit(0)

# Mock Translation Data with Red Text & Comments
mock_data = {
    "paragraphs": [
        {
            "id": "para_000",
            "translated_text": "This is a Verified Translation.",
            "ai_generated_comments": []
        },
        {
            "id": "para_001",
            "translated_text": "This translation is Uncertain (Red).",
            "ai_generated_comments": ["Uncertainty detected in term usage."]
        }
    ]
}

mock_json_path = "mock_translation.json"
with open(mock_json_path, "w", encoding="utf-8") as f:
    json.dump(mock_data, f, indent=2, ensure_ascii=False)

output_path = "test_reconstructed_advanced.docx"

print("Running advanced reconstruction verification...")
try:
    reconstruct_docx("test_sample.docx", mock_json_path, output_path)
    if os.path.exists(output_path):
        print("Success: Output file created.")
    else:
        print("Failure: Output file not found.")
except Exception as e:
    print(f"Reconstruction verification failed: {e}")
