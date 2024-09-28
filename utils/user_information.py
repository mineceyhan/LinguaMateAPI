from flask import  request, jsonify

from config import Config
from .token_processing import get_uid_from_token

def get_user_information():
    uid, error = get_uid_from_token()
    if error:
        return jsonify({'error': error}), 401
    
    try:
        # Get user data from Firestore
        user_ref = Config.db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return jsonify({'user_info': user_data}), 200
        else:
            return jsonify({'error': 'User not found.'}), 404

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
