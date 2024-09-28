import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Çevresel değişkenleri yükle
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    firestore = firestore
    db = firestore.client()
    auth = firebase_admin.auth

