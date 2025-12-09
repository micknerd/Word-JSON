import json
import os
import sys
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_bedrock_client():
    """Initializes Bedrock Runtime client."""
    # Assuming credentials are in env vars or ~/.aws/credentials
    return boto3.client(
        service_name='bedrock-runtime', 
        region_name=os.environ.get("AWS_REGION", "us-east-1")
    )

def translate_segments(data, glossary=None, context_info=None):
    """
    Translates the segments using AWS Bedrock (Claude 3).
    
    Args:
        data (dict): The JSON data containing paragraphs.
        glossary (dict, optional): Dictionary of "Term": "Translation".
        context_info (dict, optional): Metadata like project_name, member_names, etc.
    """
    client = get_bedrock_client()
    # Use Opus model by default or from env. Note: Opus ID is 'anthropic.claude-3-opus-20240229-v1:0'
    model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-opus-20240229-v1:0")
    
    # Load System Prompt from file
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt_ifrs_translation.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    else:
        # Fallback if file missing
        system_prompt = """You are a professional translator specializing in IFRS documents."""

    # Add Context/Glossary to the prompt if provided
    additional_context = ""
    if context_info:
        additional_context += "\n[Project Context]\n"
        for k, v in context_info.items():
            additional_context += f"- {k}: {v}\n"
            
    if glossary:
        additional_context += "\n[Glossary / Terminology]\n"
        for k, v in glossary.items():
            additional_context += f"- {k} -> {v}\n"

    user_message = f"""{additional_context}

Here is the document structure to translate:
{json.dumps(data, ensure_ascii=False)}

Translate the 'text' field in each paragraph. Ensure all numeric conversions and IFRS terms are applied correctly.
"""

    # 2. Call Bedrock
    # Claude 3 Messages API format
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0
    })

    try:
        response = client.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        # Claude 3 response structure
        result_text = response_body.get('content')[0].get('text')
        
        # Parse the JSON from the text response
        # Claude might wrap it in ```json ... ``` or just text.
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = result_text[start:end]
            return json.loads(json_str)
        else:
            print("Could not find JSON in response", file=sys.stderr)
            print(result_text, file=sys.stderr)
            return None

    except Exception as e:
        print(f"Bedrock Translation failed: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    # Test stub
    sample_data = {
        "paragraphs": [
            {
                "id": "p1",
                "text": "当社はIFRSを適用する。",
                "comments": []
            }
        ]
    }
    # Mock context
    ctx = {"Project": "Alpha", "CEO": "Taro Yamada"}
    gls = {"当社": "The Company", "適用する": "adopt"}
    
    try:
        # Note: This will fail if no AWS creds are set
        res = translate_segments(sample_data, glossary=gls, context_info=ctx)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Test run failed (expected if no creds): {e}")
