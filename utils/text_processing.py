#utils/text_processing.py

import json
import httpx
import openai
import os
import uuid
from ..config import Config

openai.api_key = Config.OPENAI_API_KEY

def generate_unique_filename(extension='mp3'):
    """Generate a unique filename."""
    return f"{uuid.uuid4()}.{extension}"

def text_to_speech(text_data):
    print(text_data)
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        'Authorization': f'Bearer {openai.api_key}',
    }

    content_data = json.dumps({
        "model": "tts-1",
        "input": text_data,
        "voice": "fable"
    })
    json_content = json.loads(content_data)
    
    try:
        resp = httpx.post(url=url, headers=headers, json=json_content, timeout=60)
        resp.raise_for_status()  # Ensure we catch HTTP errors
        
        # Verify content type
        if 'audio/mpeg' not in resp.headers.get('Content-Type', ''):
            raise ValueError("Invalid content type in response")
        
        # Generate a unique file name
        output_file_name = generate_unique_filename()

        # Specify the directory where the file should be saved
        output_directory = os.path.join(os.getcwd(), 'files')

        # Create the directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Full path to save the file
        output_file_path = os.path.join(output_directory, output_file_name)

        with open(output_file_path, 'wb') as f:
            f.write(resp.content)
        
        return output_file_path
    
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except ValueError as e:
        print(f"Value error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None
