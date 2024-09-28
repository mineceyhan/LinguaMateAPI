from datetime import time
import os
import sys
from flask import Flask, json, jsonify, request
import requests
import time
from .token_processing import get_uid_from_token

#* PYTHONPATH ayarınızda proje kök dizini yok . Bu nedenle config modülü içe aktarılamıyor. Projenin kök dizinini sys.path'a eklemek gerekiyor.

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config 
api_key = Config.FIREBASE_API_KEY  

def verify_token(id_token):
    try:
        decoded_token = Config.auth.verify_id_token(id_token)
        print(f'Token is valid. User ID: {decoded_token["uid"]}')
        return decoded_token
    except Config.auth.InvalidIdTokenError:
        print('Invalid ID Token')
        return None
    except Config.auth.ExpiredIdTokenError:
        print('Expired ID Token')
        return None
    except Exception as e:
        print(f'Error: {str(e)}')
        return None
    
def send_verification_email(id_token):
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}'
    data = {
        "requestType": "VERIFY_EMAIL",
        "idToken": id_token
    }

    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
        response_json = response.json()
        if response.status_code == 200:
            return jsonify({'message': 'Verification email sent successfully'}), 200  
        else:
            error_message = response_json.get('error', {}).get('message', 'No error message found')
            return {'error': error_message}, response.status_code 
    except Exception as e:
        return {'error': str(e)}, 400 
    
def signUp():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        
        auth_data = {
            'email': email,
            'password': password,
            'returnSecureToken': True
        }
        
        response = requests.post(auth_url, json=auth_data)
        if response.status_code != 200:
            return jsonify({'error': response.json()}), 401
        user_info = response.json()
        
        uid = user_info['localId']
        id_token = user_info['idToken']

        verify_token(id_token)
        result, status_code = send_verification_email(id_token)

        if(status_code != 200):
            return result
        # add firestore
        user_ref = Config.db.collection('users').document(uid)
        user_ref.set({
            'email': email,
            'name': name,
            'verified': False  
        })

        data = {
            'user_id': uid,
            'email': email,
        }
        
        return jsonify({'user_info': user_info}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

def signIn():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Firebase Authentication ile kullanıcıyı doğrula
        api_key = Config.FIREBASE_API_KEY
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        
        auth_data = {
            'email': email,
            'password': password,
            'returnSecureToken': True
        }
        
        response = requests.post(auth_url, json=auth_data)
        if response.status_code != 200:
            return jsonify({'error': 'Geçersiz e-posta veya şifre'}), 401
        
        user_info = response.json()
        uid = user_info['localId']

        # E-posta doğrulama durumunu kontrol et
        check_response = check_email_verified(uid)
        if check_response[1] != 200:
            return check_response
        
        return jsonify({'user_info': user_info}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def logout():
    uid, error = get_uid_from_token()
    if error:
        return jsonify({'error': error}), 401

    try:
        # Kullanıcının refresh tokenlarını iptal et
        Config.auth.revoke_refresh_tokens(uid)

        # Kullanıcının geçerli idToken'ını süresi dolmuş kabul et (logout zamanı)
        logout_timestamp = int(time.time() * 1000)  # Şu anki zaman (milisaniye)
        user_ref = Config.db.collection('users').document(uid)
        user_ref.update({
            'logout_time': logout_timestamp
        })
        # Kullanıcıya logout başarılı mesajı gönder
        return jsonify({
            "message": "Logout successful. All sessions have been invalidated.",
            "meta": {
                "logout_time": logout_timestamp
            }
        }), 200
    except Exception as e:
        print(str(e))
        return jsonify({"error": f"Logout failed"}), 500

def check_email_verified(uid):
    try:
        user = Config.auth.get_user(uid)
        if user.email_verified:
            # Firestore'da kullanıcı verisini güncelle
            user_ref = Config.db.collection('users').document(uid)
            user_ref.update({'verified': True})
            return jsonify({'message': 'Email verified successfully.'}), 200
        else:
            return jsonify({'message': 'Email not verified yet.'}), 400
    except Config.auth.UserNotFoundError:
        return jsonify({'error': 'User not found.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def send_password_reset_email():
    data = request.get_json()
    email = data.get('email')
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}'

    if not email:
        return jsonify({"error": "Email is required"}), 400

    data = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }

    response = requests.post(url, headers={"Content-Type": "application/json"},  data=json.dumps(data))
    
    if response.status_code == 200:
        return jsonify({"message": "Password reset email sent"}), 200
    else:
        return jsonify(response.json()), response.status_code

#todo : confirm_password_reset
#* Genel Süreç
#* Kullanıcı şifre sıfırlama talebi gönderir (Flutter'da).
#* Flask API, Firebase'e şifre sıfırlama e-postası gönderir.
#* Kullanıcı e-posta bağlantısına tıklar ve uygulama deep linking ile açılır.
#* Flutter uygulaması URL'deki oobCode'ı alır ve şifre sıfırlama sayfasına yönlendirir.
#* Kullanıcı yeni şifreyi girer ve Flutter uygulaması bu bilgileri Flask API'ye gönderir.
#* Flask API, Firebase'e şifre sıfırlama işlemini tamamlar.
def confirm_password_reset():
    data = request.get_json()
    oob_code = data.get('oobCode')
    new_password = data.get('newPassword')
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={api_key}'

    if not oob_code or not new_password:
        return jsonify({"error": "oobCode and newPassword are required"}), 400

    data = {
        "oobCode": oob_code,
        "newPassword": new_password
    }

    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))

    if response.status_code == 200:
        return jsonify({"message": "Password reset successful"}), 200
    else:
        return jsonify(response.json()), response.status_code
