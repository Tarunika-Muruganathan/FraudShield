import hashlib
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
CHUNK_SIZE = 64 * 1024  # 64 KB


def sanitize_filename(filename: str) -> str:
    """Extracts only the filename (preventing path traversal) and sanitizes special characters."""
    base_name = Path(filename).name
    sanitized = re.sub(r"[^a-zA-Z0-9_.-]", "_", base_name)
    return sanitized if sanitized else "evidence_file"


def validate_file_metadata(upload_file: UploadFile) -> str:
    """Validates original filename, extension, and content type."""
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    clean_filename = sanitize_filename(upload_file.filename)
    extension = Path(clean_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{extension}' is not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    content_type = (upload_file.content_type or "").lower().split(";")[0].strip()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{upload_file.content_type}' is not supported. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}.",
        )

    return clean_filename


async def save_evidence_file(upload_file: UploadFile) -> tuple[str, str, str, int, str]:
    """
    Saves an uploaded file to storage while calculating SHA-256 and validating size.
    Returns:
        tuple: (original_filename, stored_filename, sha256_hash, file_size, content_type)
    """
    clean_original_name = validate_file_metadata(upload_file)
    stored_filename = f"{uuid.uuid4().hex}_{clean_original_name}"
    target_path = (STORAGE_DIR / stored_filename).resolve()

    # Guard against path traversal outside the storage directory
    if not target_path.is_relative_to(STORAGE_DIR.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsafe file path detected.",
        )

    hasher = hashlib.sha256()
    total_size = 0

    try:
        with open(target_path, "wb") as out_file:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds maximum allowed size of 10MB.",
                    )

                hasher.update(chunk)
                out_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

    except Exception:
        # Clean up partial or invalid file
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise

    content_type = (upload_file.content_type or "").lower().split(";")[0].strip()
    return clean_original_name, stored_filename, hasher.hexdigest(), total_size, content_type


def get_evidence_file_path(stored_filename: str) -> Path:
    """Resolves and validates that the file exists inside the storage directory."""
    target_path = (STORAGE_DIR / stored_filename).resolve()

    if not target_path.is_relative_to(STORAGE_DIR.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path requested.",
        )

    if not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found on disk.",
        )

    return target_path


def delete_stored_file(stored_filename: str) -> bool:
    """Safely deletes a physical file from the storage directory."""
    try:
        target_path = (STORAGE_DIR / stored_filename).resolve()
        if target_path.is_relative_to(STORAGE_DIR.resolve()) and target_path.is_file():
            target_path.unlink()
            return True
    except Exception:
        pass
    return False
