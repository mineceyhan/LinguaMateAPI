#app.py

from datetime import datetime
import uuid
from flask import Flask, jsonify, request
from firebase_admin import  firestore

from .utils import send_verification_email
from .config import Config
from .utils import  translate as tr
from .utils import  text_to_speech
from .utils import  upload_to_storage
from .utils import  signUp
from .utils import  signIn
from .utils import  logout
from .utils import  refresh_id_token
from .utils import  send_password_reset_email
from .utils import  confirm_password_reset
from .utils import get_history_translation
from .utils import get_uid_from_token
from .utils import get_user_information

app = Flask("translate_app")

@app.route('/register', methods=['POST'])
def register():
    return signUp()

@app.route('/login', methods=['POST'])
def login():
    return signIn()

@app.route('/logout', methods=['GET'])
def logOut():
    return logout()

@app.route('/send_verification_email', methods=['POST'])
def sendVerificationEmail():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Authorization token is missing or invalid.'
    
    token = auth_header.split('Bearer ')[1]
    
    result, status_code = send_verification_email(token)
    return result, status_code  

@app.route('/refresh_token', methods=['POST'])
def refreshToken():
    return refresh_id_token()

@app.route('/send_password_reset_email', methods=['POST'])
def sendPasswordResetEmail():
    return send_password_reset_email()

@app.route('/confirm_password_reset', methods=['POST'])
def confirmPasswordReset():
    return confirm_password_reset()

@app.route('/translate', methods=['POST'])
def translate():
    uid, error = get_uid_from_token()
    
    if request.headers.get('Authorization') and error:
        return jsonify({'error': error}), 401
    
    data = request.get_json()
    text_to_translate = data.get('text', '')
    target_language = data.get('target_language', '')
    source_language = data.get('source_language', '')

    if not isinstance(text_to_translate, str):
        return jsonify({"error": "Invalid text format. Must be a string."}), 400

    translated_text = tr(text_to_translate, target_language)
    
    if translated_text and translated_text != "Translation failed.":
        output_file_path = text_to_speech(translated_text)
        
        if output_file_path:
            # Dosyayı Cloud Storage'a yükle
            audio_file_name = f"{uid}_{str(uuid.uuid4())}.wav"
            audio_url, error_message = upload_to_storage(output_file_path, audio_file_name, uid)
            
            if audio_url:
                # Token varsa Firestore'a kaydetme işlemi
                if uid:
                    doc_id = str(uuid.uuid4())
                    user_ref = Config.db.collection('users').document(uid)
                    
                    user_ref.collection('history').document(doc_id).set({
                        'source_language': source_language,
                        'target_language': target_language,
                        'text_to_translate': text_to_translate,
                        'translated_text': translated_text,
                        'audio_url': audio_url,  # Ses dosyasının URL'si
                        'timestamp': firestore.SERVER_TIMESTAMP
                    })
                
                return jsonify({
                    "message": "Translation successful.",
                    "data": {
                        'source_language': source_language,
                        'target_language': target_language,
                        'text_to_translate': text_to_translate,
                        'translated_text': translated_text,
                        'audio_url': audio_url  # Flutter'da bu URL kullanılarak ses oynatılır
                    },
                    "meta": {
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }), 200
            else:
                return jsonify({"error": error_message}), 500  # Hata detayını doğrudan döndür
        else:
            return jsonify({"error": "File could not be created."}), 500
    else:
        return jsonify({"error": "Translation failed."}), 500

    
@app.route('/history_translate', methods=['GET'])
def historyTtranslate():
    return get_history_translation()

@app.route('/user_information', methods=['GET'])
def getUserInformation():
    return get_user_information()
