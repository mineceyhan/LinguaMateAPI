#utils/openai_client.py

import os
import openai
import requests
from ..config import Config

openai.api_key = Config.OPENAI_API_KEY

def upload_to_storage(file_path, file_name, uid):
    bucket_url = f"https://firebasestorage.googleapis.com/v0/b/translationapp-df485.appspot.com/o" 
    upload_url = f"{bucket_url}/{file_name}?uploadType=media&name={file_name}"

    headers = {
        'Authorization': f'Bearer {uid}',
        'Content-Type': 'audio/wav',
    }

    try:
        with open(file_path, 'rb') as audio_file:
            response = requests.post(upload_url, headers=headers, data=audio_file)

        if response.status_code == 200:
            # Başarılı yükleme durumunda dosya URL'sini döndür
            return f"{bucket_url}/{file_name}?alt=media",None
        else:
            # Hata oluştuğunda hata mesajını ve HTTP durum kodunu döndür
            return None, f"Failed to upload audio file. Error: {response.text}, Status Code: {response.status_code}"
    except Exception as e:
        # Beklenmeyen bir hata oluştuğunda detaylı hata mesajı döndür
        return None, f"An error occurred: {str(e)}"


def translate(content, lang):
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4o-2024-05-13',
            messages=[
                {"role": "system", "content": "You are a translator. Translate the given text into the desired language."},
                {"role": "user", "content": f"{content} Translate this sentence into {lang}. Only provide the translated content as the response."}
            ],
            top_p=0.3,
            temperature=0.3,
            n=1,
            presence_penalty=0.5,
            frequency_penalty=0.5,
            stop=None,
        )

        text = response.choices[0].message.content
        return text
    
    except Exception as e:
        print(f"An error occurred during translation: {e}")
        return None


