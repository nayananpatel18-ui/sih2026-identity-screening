"""Single Firebase Admin boundary, with an explicit local-development fallback."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import os
from urllib.parse import quote

from app.core.config import settings

_firestore_client = None
_storage_bucket = None
_is_firebase_initialized = False
_initialization_error: str | None = None


def init_firebase() -> bool:
    """Initialize Admin SDK once; absent local credentials are an expected condition."""
    global _firestore_client, _storage_bucket, _is_firebase_initialized, _initialization_error
    if _is_firebase_initialized:
        return True
    credential_path = settings.FIREBASE_CREDENTIALS_PATH
    if credential_path and not os.path.exists(credential_path):
        _initialization_error = f"Firebase credential file not found: {credential_path}"
        return False
    if not credential_path and not settings.FIREBASE_USE_APPLICATION_DEFAULT:
        _initialization_error = "Firebase credentials are not configured (local fallback active)."
        return False
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        if not firebase_admin._apps:
            options = {key: value for key, value in {
                "projectId": settings.FIREBASE_PROJECT_ID,
                "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
            }.items() if value}
            credential = credentials.Certificate(credential_path) if credential_path else credentials.ApplicationDefault()
            firebase_admin.initialize_app(credential, options)
        _firestore_client = firestore.client()
        _storage_bucket = storage.bucket() if settings.FIREBASE_STORAGE_BUCKET else None
        _is_firebase_initialized = True
        _initialization_error = None
        return True
    except Exception as exc:
        _initialization_error = f"Firebase Admin initialization failed: {exc}"
        return False


def firebase_status() -> Dict[str, Any]:
    return {"available": _is_firebase_initialized, "mode": "firebase" if _is_firebase_initialized else "local_fallback", "error": _initialization_error}


def verify_id_token(token: str) -> Dict[str, Any]:
    if not _is_firebase_initialized:
        raise RuntimeError("Firebase authentication is unavailable; configure Firebase Admin credentials.")
    try:
        from firebase_admin import auth
        return auth.verify_id_token(token)
    except Exception as exc:
        raise ValueError("Firebase ID token verification failed") from exc


def _safe_officer_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove synthetic evaluation labels before normal screening persistence."""
    excluded = {"ground_truth", "expected_risk", "tamper_details", "is_tampered"}
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in excluded}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value
    return clean(data)


class FirestoreRepository:
    """User-owned screening/upload records in Firestore or local in-memory fallback."""
    _in_memory_store: Dict[str, Dict[str, Any]] = {}
    _in_memory_uploads: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def save_screening(cls, screening_id: str, data: Dict[str, Any], user_id: str) -> bool:
        record = _safe_officer_payload(dict(data))
        record.update({"screening_id": screening_id, "user_id": user_id, "schema_version": "m14", "persisted_at": datetime.now(timezone.utc).isoformat()})
        cls._in_memory_store[screening_id] = record
        if _is_firebase_initialized and _firestore_client:
            _firestore_client.collection("screenings").document(screening_id).set(record)
        return True

    @classmethod
    def get_screening(cls, screening_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        record = None
        if _is_firebase_initialized and _firestore_client:
            doc = _firestore_client.collection("screenings").document(screening_id).get()
            record = doc.to_dict() if doc.exists else None
        else:
            record = cls._in_memory_store.get(screening_id)
        return record if record and record.get("user_id") == user_id else None

    @classmethod
    def save_upload(cls, upload_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        record = dict(data, upload_id=upload_id, user_id=user_id, schema_version="m14", created_at=datetime.now(timezone.utc).isoformat())
        cls._in_memory_uploads[upload_id] = record
        if _is_firebase_initialized and _firestore_client:
            _firestore_client.collection("uploads").document(upload_id).set(record)
        return record

    @classmethod
    def get_upload(cls, upload_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        record = cls._in_memory_uploads.get(upload_id)
        if _is_firebase_initialized and _firestore_client:
            doc = _firestore_client.collection("uploads").document(upload_id).get()
            record = doc.to_dict() if doc.exists else None
        return record if record and record.get("user_id") == user_id else None

    @classmethod
    def is_connected(cls) -> bool:
        return _is_firebase_initialized


class FirebaseStorageService:
    """Private user-scoped storage; public download URLs are never created."""
    LOCAL_DIR = Path("temp_uploads")

    @classmethod
    def upload(cls, *, user_id: str, upload_id: str, filename: str, content_type: str, contents: bytes) -> Dict[str, Any]:
        # Firebase UIDs are authoritative, but encode them before using them as
        # an object/directory segment so local fallback cannot be path-traversed.
        storage_user_id = quote(user_id, safe="")
        object_path = f"users/{storage_user_id}/uploads/{upload_id}/{filename}"
        if _is_firebase_initialized and _storage_bucket:
            blob = _storage_bucket.blob(object_path)
            blob.upload_from_string(contents, content_type=content_type)
            return {"storage_provider": "firebase", "storage_path": object_path}
        if not settings.FIREBASE_LOCAL_FALLBACK:
            raise RuntimeError("Firebase Storage is unavailable and local fallback is disabled.")
        target = cls.LOCAL_DIR / storage_user_id / upload_id / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
        return {"storage_provider": "local_fallback", "storage_path": str(target)}
