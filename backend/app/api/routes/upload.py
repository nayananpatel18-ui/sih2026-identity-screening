"""
Upload Route — Handles temporary local document intake.
Files are stored in a local temp_uploads/ directory.
No real identity documents are processed.
"""

import io
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

router = APIRouter()

TEMP_UPLOAD_DIR = "temp_uploads"
ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/webp": "webp",
}
ALLOWED_IMAGE_FORMATS = {"png", "jpeg", "webp"}


def _ensure_upload_dir():
    Path(TEMP_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def _sanitize_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")

    safe_name = os.path.basename(filename.strip())
    if safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename provided.")

    return safe_name


def _normalize_extension(extension: str) -> str:
    normalized = (extension or "").lower().lstrip(".")
    if normalized == "jpg":
        return "jpeg"
    return normalized


def _validate_image_file(file: UploadFile, contents: bytes) -> tuple[str, str]:
    original_filename = _sanitize_filename(file.filename)
    file_extension = _normalize_extension(Path(original_filename).suffix)

    if file_extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {original_filename}. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}."
        )

    declared_content_type = (file.content_type or "").lower()
    if declared_content_type and declared_content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {declared_content_type}. Allowed: image/png, image/jpeg, image/webp."
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > settings.UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds the demo-safe limit of {settings.UPLOAD_MAX_BYTES} bytes."
        )

    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable image.") from None

    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.load()
            actual_format = (image.format or "").lower()
            if actual_format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(status_code=400, detail="Uploaded file is not a supported image format.")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Uploaded file could not be validated as a supported image.") from None

    if actual_format == "jpeg":
        valid_extensions = {"jpeg", "jpg"}
    else:
        valid_extensions = {actual_format}

    if file_extension not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file content does not match the provided extension. Expected one of: {', '.join(sorted(valid_extensions))}."
        )

    return actual_format, declared_content_type or f"image/{actual_format}"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "primary_document"
):
    """
    Accepts an uploaded image file and stores it temporarily for local demo use.
    The upload is intentionally limited to demo-safe image types and does not perform
    OCR, biometric verification, or external analysis.
    """
    _ensure_upload_dir()

    contents = await file.read()
    image_format, detected_content_type = _validate_image_file(file, contents)

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{image_format if image_format != 'jpeg' else 'jpg'}"
    save_path = Path(TEMP_UPLOAD_DIR) / filename

    with save_path.open("wb") as destination:
        destination.write(contents)

    return {
        "file_id": file_id,
        "upload_session_id": file_id,
        "doc_type": doc_type,
        "original_filename": _sanitize_filename(file.filename),
        "size_bytes": len(contents),
        "content_type": detected_content_type,
        "status": "UPLOADED",
    }
