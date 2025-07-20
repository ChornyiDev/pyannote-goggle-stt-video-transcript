import firebase_admin
from firebase_admin import credentials, firestore
import os

cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

db = firestore.client()

def update_firestore(doc_ref, data):
    doc_path = doc_ref.split('/')
    db.collection(doc_path[0]).document(doc_path[1]).set(data, merge=True)
