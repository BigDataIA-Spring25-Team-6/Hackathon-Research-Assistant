from dotenv import load_dotenv
from mistralai import Mistral
import os
from openai import OpenAI
from PIL import Image
from base64 import b64decode



load_dotenv()
mistral_key = os.getenv("MISTRAL_API_KEY")
open_ai_key = os.getenv("OPENAI_API_KEY")
mistral = Mistral(api_key=mistral_key)
openai_client = OpenAI(api_key=open_ai_key)

def analyze_prompt(prompt:str, max_length:int =900) -> str:
    """
    Generates concise DALL-E 3 specs within character limits
    """
    compression_prompt = f"""Convert this query into DALL-E 3 specs STRICTLY under {max_length} chars:
    {prompt}
    
    Use these rules:
    1. Prioritize visual elements over text descriptions
    2. Use abbreviations: "&" instead of "and", "vs" instead of "versus"
    3. Avoid markdown formatting
    4. Structure: [Style][Key Elements][Layout][Colors]
    """
    response = mistral.chat.complete(
        model="pixtral-12b-2409",
        messages=[{
            "role": "user",
            "content": [{
                "type": "text",
                "text": compression_prompt
            }]
        }],
        max_tokens=300
    )
    generated = response.choices[0].message.content
    return clean_prompt(generated,max_length)

def clean_prompt(text:str,max_length:int) -> str:

    """Ensures prompt compliance"""
    replacements = {
        "**": "", "## ": "", "- ": "",
        "the image should": "",
        "please note that": ""
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Trim to max length at sentence boundary
    if len(text) > max_length:
        return text[:max_length].rsplit('.', 1)[0] + '.' 
    return text


def generate_image_dalle(image_spec: str) -> Image.Image:
    """Generate image using DALL-E 2 API"""
    response = openai_client.images.generate(
        model="dall-e-2",
        prompt=image_spec,
        size="1024x1024", 
        quality="standard", 
        style="vivid",     
        n=1,
        response_format="b64_json",
    )
    
    # Download image from URL
    for index, image_dict in enumerate(response.data):
        image_data = b64decode(image_dict.b64_json)
        image_file = f"image-{index}.png"
        with open(image_file, mode="wb") as png:
            png.write(image_data)

    print("Images Saved")
    return

def image_agent(prompt: str):
    refined_prompt = analyze_prompt(prompt)
    return generate_image_dalle(refined_prompt)

# Example usage
prompt = "Top 5 products sold in amazon and walmart in 2021"
result_image = image_agent(prompt)







