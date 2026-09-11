"""Focused M14 tests: no Firebase credentials, network, or emulator required."""

import asyncio
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
from app.api.dependencies import auth
from app.services import firebase_service


class FirebaseInfrastructureTests(TestCase):
    def setUp(self):
        firebase_service._is_firebase_initialized = False
        firebase_service._firestore_client = None
        firebase_service._storage_bucket = None
        firebase_service.FirestoreRepository._in_memory_store.clear()
        firebase_service.FirestoreRepository._in_memory_uploads.clear()

    def test_auth_rejects_missing_and_malformed_bearer_tokens(self):
        with self.assertRaises(HTTPException) as missing:
            asyncio.run(auth.require_authenticated_principal(None))
        self.assertEqual(missing.exception.status_code, 401)
        with self.assertRaises(HTTPException) as malformed:
            asyncio.run(auth.require_authenticated_principal("Basic abc"))
        self.assertEqual(malformed.exception.status_code, 401)

    def test_auth_extracts_verified_firebase_principal(self):
        with patch.object(auth, "verify_id_token", return_value={"uid": "user-a", "email": "a@example.test"}):
            principal = asyncio.run(auth.require_authenticated_principal("Bearer verified-token"))
        self.assertEqual(principal.uid, "user-a")
        self.assertEqual(principal.email, "a@example.test")

    def test_auth_reports_unconfigured_firebase(self):
        with patch.object(auth, "verify_id_token", side_effect=RuntimeError("not configured")):
            with self.assertRaises(HTTPException) as unavailable:
                asyncio.run(auth.require_authenticated_principal("Bearer token"))
        self.assertEqual(unavailable.exception.status_code, 503)

    def test_screening_persistence_is_owned_and_removes_ground_truth(self):
        firebase_service.FirestoreRepository.save_screening("screening-a", {
            "risk_level": "GREEN", "ground_truth": {"is_tampered": False},
            "nested": {"expected_risk": "GREEN", "safe": True},
        }, "user-a")
        saved = firebase_service.FirestoreRepository.get_screening("screening-a", "user-a")
        self.assertEqual(saved["user_id"], "user-a")
        self.assertNotIn("ground_truth", saved)
        self.assertNotIn("expected_risk", saved["nested"])
        self.assertIsNone(firebase_service.FirestoreRepository.get_screening("screening-a", "user-b"))

    def test_upload_metadata_is_owned_and_linkable(self):
        saved = firebase_service.FirestoreRepository.save_upload("upload-a", {
            "original_filename": "passport.png", "storage_path": "users/user-a/uploads/upload-a/passport.png",
            "screening_id": None, "status": "UPLOADED",
        }, "user-a")
        self.assertEqual(saved["upload_id"], "upload-a")
        self.assertIsNone(firebase_service.FirestoreRepository.get_upload("upload-a", "user-a")["screening_id"])
        self.assertIsNone(firebase_service.FirestoreRepository.get_upload("upload-a", "user-b"))

    def test_local_storage_fallback_is_private_and_user_scoped(self):
        with patch.object(firebase_service.FirebaseStorageService, "LOCAL_DIR", Path("temp_uploads_test")):
            result = firebase_service.FirebaseStorageService.upload(
                user_id="user-a", upload_id="upload-a", filename="image.png", content_type="image/png", contents=b"image",
            )
            self.assertEqual(result["storage_provider"], "local_fallback")
            self.assertEqual(Path(result["storage_path"]).read_bytes(), b"image")
            self.assertIn("user-a", result["storage_path"])
            Path(result["storage_path"]).unlink()
            Path(result["storage_path"]).parent.rmdir()
            Path(result["storage_path"]).parent.parent.rmdir()
            Path(result["storage_path"]).parent.parent.parent.rmdir()

    def test_local_storage_encodes_uid_before_constructing_a_path(self):
        with patch.object(firebase_service.FirebaseStorageService, "LOCAL_DIR", Path("temp_uploads_test")):
            result = firebase_service.FirebaseStorageService.upload(
                user_id="user/../other", upload_id="upload-a", filename="image.png", content_type="image/png", contents=b"image",
            )
            self.assertIn("user%2F..%2Fother", result["storage_path"])
            self.assertEqual(Path(result["storage_path"]).read_bytes(), b"image")
            Path(result["storage_path"]).unlink()
            Path(result["storage_path"]).parent.rmdir()
            Path(result["storage_path"]).parent.parent.rmdir()
            Path(result["storage_path"]).parent.parent.parent.rmdir()

    def test_firebase_unavailable_status_is_explicit(self):
        with patch.object(firebase_service.settings, "FIREBASE_CREDENTIALS_PATH", None), patch.object(firebase_service.settings, "FIREBASE_USE_APPLICATION_DEFAULT", False):
            self.assertFalse(firebase_service.init_firebase())
        status = firebase_service.firebase_status()
        self.assertEqual(status["mode"], "local_fallback")
        self.assertFalse(status["available"])


if __name__ == "__main__":
    import unittest
    unittest.main()
