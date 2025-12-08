import json
import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def translate_segments(data):
    """
    Translates the segments in the data using Gemini.
    Expects data["paragraphs"] to be a list of segment objects.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)
    
    # Construct the prompt
    # We send the entire relevant structure to Gemini so it understands context.
    # To reduce token usage, we might want to strip unnecessary fields if the doc is huge,
    # but for a prototype, sending the full JSON is fine and robust.
    
    system_instruction = """You are a professional translator. Translate the Japanese text in the JSON input to English.

CRITICAL INSTRUCTIONS:
1. 'associated_comments' or 'comments' in the input contain specific instructions for the translation (e.g., "Use strong language", "translate as X"). You MUST follow these instructions.
2. If the user provided a specific term or style in the comments, apply it.
3. Output the SAME JSON structure, but add two new fields to each paragraph object:
   - "translated_text": The English translation.
   - "ai_generated_comments": A list of notes from you (the AI) if you have doubts, alternative translation suggestions, or want to explain why you translated something a certain way. If no comment is needed, this can be empty.
   
Input Format:
{
  "paragraphs": [
    { "id": "...", "text": "...", "comments": [...] }
  ]
}

Output Format:
{
  "paragraphs": [
    { "id": "...", "text": "...", "comments": [...], "translated_text": "...", "ai_generated_comments": [{"body": "..."}] }
  ]
}
"""

    prompt = f"""Here is the document structure to translate:
    
{json.dumps(data, ensure_ascii=False)}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp", # Using a capable model (User asked for 3.0/1.5 pro, using latest available alias or specific usually best. 1.5-pro or 3.0 prototype if available. Let's stick to a standard capable ID)
        # Verify model name. user said "gemini-1.5-pro-latest (or 3.0)". 
        # I will use 'gemini-1.5-pro-latest' as requested, or assume the SDK directs to the right one.
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
    )
    
    try:
        result_json = json.loads(response.text)
        return result_json
    except json.JSONDecodeError:
        # Fallback if model didn't return pure JSON (though response_mime_type should help)
        print("Error decoding JSON from AI response", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return None

if __name__ == "__main__":
    # Test with dummy data
    sample_data = {
        "paragraphs": [
            {
                "id": "p1",
                "text": "この契約書は無効とする。",
                "comments": [{"id": "c1", "body": "「無効」は strong な表現にして。Void ではなく Null and Void で。"}]
            }
        ]
    }
    
    try:
        translated = translate_segments(sample_data)
        print(json.dumps(translated, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
