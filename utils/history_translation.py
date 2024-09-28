import os
import sys
from flask import  request, jsonify
import firebase_admin

from .token_processing import get_uid_from_token

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..config import Config


def get_history_translation():
    uid, error = get_uid_from_token()
    if error:
        return jsonify({'error': error}), 401

    try:
        history_ref = Config.db.collection('users').document(uid).collection('history')
        history_docs = history_ref.order_by('timestamp',  direction=Config.firestore.Query.DESCENDING).stream()
        
        # Verileri JSON formatında döndür
        history_list = [doc.to_dict() for doc in history_docs]
        
        return jsonify({'history': history_list}), 200

    except Config.auth.AuthError as e:
        return jsonify({'error': f'Authentication error: {str(e)}'}), 401
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
