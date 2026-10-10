"""
File handling utilities: saving uploads, converting PDFs to images,
and cleaning up temporary files.
"""

import os
import uuid
from typing import List

from pdf2image import convert_from_path

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload_file(file_bytes: bytes, original_filename: str) -> str:
    """Saves uploaded file bytes to disk with a unique name and returns the path."""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)
    return dest_path


def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[str]:
    """
    Converts every page of a PDF into a PNG image (Phase 1: PDF processing).
    Requires Poppler to be installed and on the system PATH.
    """
    pages = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []
    for i, page in enumerate(pages):
        out_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_page{i + 1}.png")
        page.save(out_path, "PNG")
        image_paths.append(out_path)
    return image_paths


def is_pdf(filename: str) -> bool:
    return filename.lower().endswith(".pdf")


def cleanup_files(paths: List[str]) -> None:
    """Best-effort deletion of temporary files (page images etc.)."""
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
