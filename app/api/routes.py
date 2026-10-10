"""
REST API Routes for the Certificate OCR System.

Core endpoints:
    GET  /health                    - health check
    POST /upload                    - upload a certificate (no processing)
    POST /extract                   - upload + full OCR + extraction (one step)
    GET  /results/{id}               - fetch a previously extracted result
    DELETE /documents/{id}           - delete a stored result

Bonus feature endpoints:
    POST /batch-extract              - process multiple certificates at once
    GET  /export/excel               - download all results as an .xlsx file
    GET  /certificates/{id}/qrcode    - get a QR code encoding the result
    GET  /audit-log                  - view the processing audit trail
    GET  /languages                  - list supported OCR languages
"""

import os
import time
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.ocr_engine import run_ocr, run_ocr_multi_page, SUPPORTED_LANGUAGES
from app.core.extractor import extract_fields
from app.utils.file_handler import save_upload_file, pdf_to_images, is_pdf, cleanup_files
from app.utils.validators import validate_file
from app.utils.qr_generator import generate_qr_for_certificate
from app.utils.excel_export import export_certificates_to_excel
from app.models.database import get_db, Certificate, AuditLog

router = APIRouter()


def _log_audit(db: Session, filename: str, action: str, status: str,
               certificate_id: str = None, details: str = ""):
    entry = AuditLog(
        certificate_id=certificate_id,
        filename=filename,
        action=action,
        status=status,
        details=details,
    )
    db.add(entry)
    db.commit()


def _process_single_file(file: UploadFile, lang: str, db: Session) -> Certificate:
    """Shared pipeline: validate -> save -> (pdf->image) -> OCR -> extract -> store."""
    file_bytes = file.file.read()
    validate_file(file, file_bytes)

    saved_path = save_upload_file(file_bytes, file.filename)
    temp_pages: List[str] = []

    try:
        if is_pdf(saved_path):
            temp_pages = pdf_to_images(saved_path)
            ocr_result = run_ocr_multi_page(temp_pages, lang=lang)
        else:
            ocr_result = run_ocr(saved_path, lang=lang)

        fields = extract_fields(ocr_result.text)

        certificate = Certificate(
            filename=file.filename,
            candidate_name=fields.candidate_name,
            certificate_title=fields.certificate_title,
            organization_name=fields.organization_name,
            issue_date=fields.issue_date,
            certificate_number=fields.certificate_number,
            grade_score=fields.grade_score,
            duration=fields.duration,
            raw_text=ocr_result.text,
            ocr_confidence=ocr_result.confidence,
            language=lang,
        )
        db.add(certificate)
        db.commit()
        db.refresh(certificate)

        _log_audit(db, file.filename, "EXTRACT", "SUCCESS", certificate.id,
                   f"Confidence: {ocr_result.confidence}%, Words: {ocr_result.word_count}")
        return certificate

    except Exception as exc:
        _log_audit(db, file.filename, "EXTRACT", "FAILED", details=str(exc))
        raise
    finally:
        cleanup_files(temp_pages)


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@router.get("/health", tags=["Core"])
async def health_check():
    return {"status": "healthy", "service": "Certificate OCR System", "version": "1.0.0"}


@router.post("/upload", tags=["Core"])
async def upload_certificate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads and stores a file WITHOUT running OCR (useful for previews)."""
    file_bytes = file.file.read()
    validate_file(file, file_bytes)
    saved_path = save_upload_file(file_bytes, file.filename)
    _log_audit(db, file.filename, "UPLOAD", "SUCCESS")
    return {"message": "File uploaded successfully", "path": saved_path, "filename": file.filename}


@router.post("/extract", tags=["Core"])
async def extract_certificate(
    file: UploadFile = File(...),
    lang: str = Query("eng", description="Tesseract language code"),
    db: Session = Depends(get_db),
):
    """Uploads a certificate and runs the full OCR + extraction pipeline."""
    start = time.time()
    certificate = _process_single_file(file, lang, db)
    elapsed = round(time.time() - start, 2)

    return {
        "id": certificate.id,
        "filename": certificate.filename,
        "candidate_name": certificate.candidate_name,
        "certificate_title": certificate.certificate_title,
        "organization_name": certificate.organization_name,
        "issue_date": certificate.issue_date,
        "certificate_number": certificate.certificate_number,
        "grade_score": certificate.grade_score,
        "duration": certificate.duration,
        "ocr_confidence": certificate.ocr_confidence,
        "raw_text": certificate.raw_text,
        "processing_time_seconds": elapsed,
    }


@router.get("/results/{certificate_id}", tags=["Core"])
async def get_result(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "id": cert.id,
        "filename": cert.filename,
        "candidate_name": cert.candidate_name,
        "certificate_title": cert.certificate_title,
        "organization_name": cert.organization_name,
        "issue_date": cert.issue_date,
        "certificate_number": cert.certificate_number,
        "grade_score": cert.grade_score,
        "duration": cert.duration,
        "ocr_confidence": cert.ocr_confidence,
        "raw_text": cert.raw_text,
        "created_at": str(cert.created_at),
    }


@router.get("/documents", tags=["Core"])
async def list_documents(db: Session = Depends(get_db)):
    """Lists all previously processed certificates (most recent first)."""
    certs = db.query(Certificate).order_by(Certificate.created_at.desc()).all()
    return [{
        "id": c.id, "filename": c.filename, "candidate_name": c.candidate_name,
        "certificate_title": c.certificate_title, "created_at": str(c.created_at),
    } for c in certs]


@router.delete("/documents/{certificate_id}", tags=["Core"])
async def delete_document(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    db.delete(cert)
    db.commit()
    _log_audit(db, cert.filename, "DELETE", "SUCCESS", certificate_id)
    return {"message": "Certificate deleted successfully"}


# ---------------------------------------------------------------------------
# Bonus feature endpoints
# ---------------------------------------------------------------------------

@router.post("/batch-extract", tags=["Bonus Features"])
async def batch_extract(
    files: List[UploadFile] = File(...),
    lang: str = Query("eng"),
    db: Session = Depends(get_db),
):
    """Bonus Feature: Batch Processing — handles multiple certificates in one call."""
    results = []
    for file in files:
        try:
            cert = _process_single_file(file, lang, db)
            results.append({
                "filename": cert.filename, "id": cert.id, "status": "success",
                "candidate_name": cert.candidate_name,
                "certificate_title": cert.certificate_title,
                "ocr_confidence": cert.ocr_confidence,
            })
        except Exception as exc:
            results.append({"filename": file.filename, "status": "failed", "error": str(exc)})

    return {"total": len(files), "results": results}


@router.get("/export/excel", tags=["Bonus Features"])
async def export_excel(db: Session = Depends(get_db)):
    """Bonus Feature: Excel Export — downloads all extracted results as .xlsx."""
    certs = db.query(Certificate).order_by(Certificate.created_at.desc()).all()
    if not certs:
        raise HTTPException(status_code=404, detail="No certificates to export yet")
    path = export_certificates_to_excel(certs)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="certificates_export.xlsx",
    )


@router.get("/certificates/{certificate_id}/qrcode", tags=["Bonus Features"])
async def get_qr_code(certificate_id: str, db: Session = Depends(get_db)):
    """Bonus Feature: QR Code Generation — encodes the certificate's data."""
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    data = {
        "candidate_name": cert.candidate_name,
        "certificate_title": cert.certificate_title,
        "organization_name": cert.organization_name,
        "issue_date": cert.issue_date,
        "certificate_number": cert.certificate_number,
    }
    qr_path = generate_qr_for_certificate(cert.id, data)
    return FileResponse(qr_path, media_type="image/png", filename=f"{cert.id}_qrcode.png")


@router.get("/audit-log", tags=["Bonus Features"])
async def get_audit_log(db: Session = Depends(get_db), limit: int = 100):
    """Bonus Feature: Audit Trail — every upload/extract/delete event."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [{
        "id": l.id, "filename": l.filename, "action": l.action,
        "status": l.status, "details": l.details, "timestamp": str(l.timestamp),
    } for l in logs]


@router.get("/languages", tags=["Bonus Features"])
async def get_supported_languages():
    """Bonus Feature: Multi-language Support — lists OCR languages available."""
    return {"supported_languages": SUPPORTED_LANGUAGES}
