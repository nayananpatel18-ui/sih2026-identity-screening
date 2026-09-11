"""
Firebase Admin SDK wrapper service with local memory fallback.
Ensures application runs seamlessly with or without live Firebase credentials.
"""

import os
from typing import Dict, Any, Optional, List
from app.core.config import settings

_firestore_client = None
_is_firebase_initialized = False


def init_firebase():
    global _firestore_client, _is_firebase_initialized
    
    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if not os.path.exists(cred_path):
        print(f"[FirebaseService] Warning: Service account file not found at '{cred_path}'. Operating in LOCAL MOCK mode.")
        _is_firebase_initialized = False
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID
            })
        
        _firestore_client = firestore.client()
        _is_firebase_initialized = True
        print("[FirebaseService] Firestore successfully connected!")
    except Exception as e:
        print(f"[FirebaseService] Could not initialize Firebase Admin SDK: {e}. Falling back to LOCAL MOCK mode.")
        _is_firebase_initialized = False


class FirestoreRepository:
    """Safe Repository interface abstraction over Firestore / Local Memory."""

    _in_memory_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def save_screening(cls, screening_id: str, data: Dict[str, Any]) -> bool:
        cls._in_memory_store[screening_id] = data
        if _is_firebase_initialized and _firestore_client:
            try:
                _firestore_client.collection('screenings').document(screening_id).set(data)
                return True
            except Exception as e:
                print(f"[FirestoreRepository] Firestore save error: {e}")
        return True

    @classmethod
    def get_screening(cls, screening_id: str) -> Optional[Dict[str, Any]]:
        if _is_firebase_initialized and _firestore_client:
            try:
                doc = _firestore_client.collection('screenings').document(screening_id).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                print(f"[FirestoreRepository] Firestore fetch error: {e}")
        return cls._in_memory_store.get(screening_id)

    @classmethod
    def is_connected(cls) -> bool:
        return _is_firebase_initialized
