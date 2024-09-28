from flask import jsonify, request
import requests

from ..config import Config

api_key = Config.FIREBASE_API_KEY  

def refresh_id_token():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    try:
        refresh_url = f"https://identitytoolkit.googleapis.com/v1/token?key={api_key}"
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(refresh_url, data=refresh_data)
        if response.status_code != 200:
            response_data = response.json()
            error_message = response_data.get('error', {}).get('message', 'Token yenileme başarısız')
            if 'TOKEN_EXPIRED' in error_message:
                return jsonify({'error': 'Refresh token has expired, please re-authenticate.'}), 401
            return jsonify({'error': error_message}), response.status_code        
        # Yenilenen token bilgilerini döndür
        new_tokens = response.json()
        return jsonify(new_tokens), 200
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Ağ hatası: {str(e)}'}), 500
    
    except Exception as e:
        print({'error': str(e)})
        return jsonify({'error': str(e)}), 400
    
def get_uid_from_token():

    # Authorization başlığından token'ı al
    auth_header = request.headers.get('Authorization')
    
    # Authorization başlığının var olup olmadığını kontrol et
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Authorization token is missing or invalid.'
    
    # 'Bearer ' kısmını kaldırarak sadece token'ı al
    token = auth_header.split('Bearer ')[1]
    
    try:
        decoded_token = Config.auth.verify_id_token(token)
        uid = decoded_token['uid']
        return uid, None
    except Config.auth.ExpiredIdTokenError:
        return None, 'ID token has expired.'
    except Config.auth.RevokedIdTokenError:
        return None, 'ID token has been revoked.'
    except Exception as e:
        return None, f'Invalid token: {str(e)}'