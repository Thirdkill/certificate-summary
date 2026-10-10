"""
Bonus Feature: QR Code Generation

Generates a QR code encoding a certificate's extracted data (or a
verification URL). Useful for embedding a scannable verification code
onto a re-issued/digital copy of the certificate, and for quickly
sharing extraction results.
"""

import json
import os
import qrcode

QR_OUTPUT_DIR = "static/images/qrcodes"
os.makedirs(QR_OUTPUT_DIR, exist_ok=True)


def generate_qr_for_certificate(certificate_id: str, data: dict) -> str:
    """
    Generates a QR code PNG encoding the certificate's key fields as JSON
    and returns the relative path to the saved image.
    """
    payload = {
        "certificate_id": certificate_id,
        "name": data.get("candidate_name"),
        "title": data.get("certificate_title"),
        "organization": data.get("organization_name"),
        "issue_date": data.get("issue_date"),
        "certificate_number": data.get("certificate_number"),
    }

    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    out_path = os.path.join(QR_OUTPUT_DIR, f"{certificate_id}.png")
    img.save(out_path)
    return out_path
