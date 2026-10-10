"""
Unit tests for the core OCR pipeline: preprocessing, OCR extraction, and
field extraction. Run with:

    python -m pytest tests/
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.core.preprocessor import preprocess_image
from app.core.ocr_engine import run_ocr, SUPPORTED_LANGUAGES
from app.core.extractor import extract_fields, ExtractedFields

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_certificates")
SAMPLE_CERT = os.path.join(SAMPLE_DIR, "sample_01_academic_completion.png")


@pytest.fixture(scope="module")
def sample_exists():
    if not os.path.exists(SAMPLE_CERT):
        pytest.skip("Sample certificates not generated yet — run "
                     "tests/sample_certificates/generate_samples.py first")
    return True


def test_preprocess_image_returns_array(sample_exists):
    processed = preprocess_image(SAMPLE_CERT)
    assert processed is not None
    assert processed.shape[0] > 0 and processed.shape[1] > 0


def test_preprocess_invalid_path_raises():
    with pytest.raises(ValueError):
        preprocess_image("this/path/does/not/exist.png")


def test_run_ocr_extracts_text(sample_exists):
    result = run_ocr(SAMPLE_CERT, lang="eng")
    assert result.text  # some text should be found
    assert result.word_count > 0
    assert 0 <= result.confidence <= 100


def test_run_ocr_invalid_language_falls_back_to_english(sample_exists):
    result = run_ocr(SAMPLE_CERT, lang="not_a_real_lang")
    assert result.language == "eng"


def test_supported_languages_contains_english():
    assert "eng" in SUPPORTED_LANGUAGES


def test_extract_fields_finds_name_and_date(sample_exists):
    ocr_result = run_ocr(SAMPLE_CERT, lang="eng")
    fields = extract_fields(ocr_result.text)
    assert isinstance(fields, ExtractedFields)
    assert fields.candidate_name is not None
    assert fields.issue_date is not None
    assert fields.certificate_number is not None


def test_extract_fields_handles_empty_text():
    fields = extract_fields("")
    assert fields.candidate_name is None
    assert fields.certificate_title is None


def test_extract_fields_no_newline_artifacts(sample_exists):
    """Regression test: extracted values should never contain raw newlines."""
    ocr_result = run_ocr(SAMPLE_CERT, lang="eng")
    fields = extract_fields(ocr_result.text)
    for value in fields.to_dict().values():
        if value:
            assert "\n" not in value
