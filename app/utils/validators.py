"""
Input validation utilities: file type checking and size limits.
Designed to accept "all types of certificates" — every common image
format plus PDF — while rejecting anything unsafe or unsupported.
"""

from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp", ".pdf"}
MAX_FILE_SIZE_MB = 15


def validate_file(file: UploadFile, file_bytes: bytes) -> None:
    """Raises HTTPException if the uploaded file fails validation."""
    filename = file.filename or ""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed types: "
                   f"{', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed is "
                   f"{MAX_FILE_SIZE_MB} MB.",
        )

    if size_mb == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
