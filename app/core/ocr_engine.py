"""
OCR Engine (Phase 1: OCR Integration)

Thin, well-documented wrapper around pytesseract that:
    - Runs Tesseract on a preprocessed image
    - Returns both the raw extracted text AND a confidence score
    - Supports multiple languages (Bonus Feature: Multi-language Support)
    - Supports multi-page PDFs by extracting page-by-page
"""

from dataclasses import dataclass, field
from typing import List

import cv2
import pytesseract
from pytesseract import Output

from app.core.preprocessor import preprocess_image

# If Tesseract is not on the system PATH (common on Windows), uncomment and
# set the correct path below:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Languages bundled with a standard Tesseract install that this app supports
# out of the box. Install extra language packs (e.g. `tesseract-ocr-urd`)
# to extend this list.
SUPPORTED_LANGUAGES = {
    "eng": "English",
    "urd": "Urdu",
    "ara": "Arabic",
    "fra": "French",
    "spa": "Spanish",
    "deu": "German",
    "chi_sim": "Chinese (Simplified)",
    "hin": "Hindi",
}


@dataclass
class OCRResult:
    text: str
    confidence: float
    word_count: int
    language: str
    per_word_confidences: List[float] = field(default_factory=list)


def run_ocr(image_path: str, lang: str = "eng", preprocess: bool = True) -> OCRResult:
    """
    Runs Tesseract OCR on a single image and returns structured results.

    Args:
        image_path: path to the image file.
        lang: Tesseract language code (see SUPPORTED_LANGUAGES).
        preprocess: whether to run the image-enhancement pipeline first
                    (strongly recommended — see app/core/preprocessor.py).
    """
    if lang not in SUPPORTED_LANGUAGES:
        lang = "eng"

    if preprocess:
        img = preprocess_image(image_path, for_ocr=True)
    else:
        img = cv2.imread(image_path)

    # Page segmentation mode 6 = "Assume a single uniform block of text",
    # which works well for certificates. OEM 3 = default LSTM engine.
    custom_config = r"--oem 3 --psm 6"

    data = pytesseract.image_to_data(
        img, lang=lang, config=custom_config, output_type=Output.DICT
    )

    words = []
    confidences = []
    for i, word in enumerate(data["text"]):
        word = word.strip()
        conf = data["conf"][i]
        if word and str(conf) != "-1":
            words.append(word)
            try:
                confidences.append(float(conf))
            except ValueError:
                pass

    text = pytesseract.image_to_string(img, lang=lang, config=custom_config)
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    return OCRResult(
        text=text.strip(),
        confidence=avg_conf,
        word_count=len(words),
        language=lang,
        per_word_confidences=confidences,
    )


def run_ocr_multi_page(image_paths: List[str], lang: str = "eng") -> OCRResult:
    """Runs OCR across multiple page images (from a multi-page PDF) and
    concatenates the results into one OCRResult."""
    all_text = []
    all_conf = []
    total_words = 0

    for path in image_paths:
        result = run_ocr(path, lang=lang)
        all_text.append(result.text)
        all_conf.extend(result.per_word_confidences)
        total_words += result.word_count

    avg_conf = round(sum(all_conf) / len(all_conf), 2) if all_conf else 0.0

    return OCRResult(
        text="\n\n--- Page Break ---\n\n".join(all_text),
        confidence=avg_conf,
        word_count=total_words,
        language=lang,
        per_word_confidences=all_conf,
    )
