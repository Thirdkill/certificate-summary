"""
Information Extraction Engine (Phase 2: Intelligent Extraction)

Takes the raw OCR text and identifies structured fields:
    - Candidate Name
    - Certificate Title
    - Organization Name
    - Issue Date
    - Certificate Number
    - Grade / Score
    - Duration

This uses a combination of labeled-field regex matching (e.g. lines that
literally say "Name:") and heuristic pattern matching (e.g. a date-shaped
string, an all-caps line near the top being the certificate title) so it
is not tied to one exact certificate layout. This is intentionally
dependency-light (no heavy NLP model) so it runs fast and is easy to
extend for new certificate templates.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ExtractedFields:
    candidate_name: Optional[str] = None
    certificate_title: Optional[str] = None
    organization_name: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_number: Optional[str] = None
    grade_score: Optional[str] = None
    duration: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"
    r"|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}"
    r"|(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

CERT_NUMBER_PATTERN = re.compile(
    r"\b(?:certificate\s*(?:id|no\.?|number|#)?\s*[:\-]?\s*)"
    r"([A-Z0-9]{2,}[\-\/]?[A-Z0-9]{2,}(?:[\-\/][A-Z0-9]+)*)",
    re.IGNORECASE,
)

GENERIC_ID_PATTERN = re.compile(r"\b([A-Z]{2,5}-\d{3,}(?:-\d+)?)\b")

GRADE_PATTERN = re.compile(
    r"(?:grade|score|result|marks?)\s*[:\-]?\s*"
    r"([A-Za-z0-9\+\-]{1,4}%?|\d{1,3}\s*(?:%|/\s*\d{1,3})?)",
    re.IGNORECASE,
)

DURATION_PATTERN = re.compile(
    r"(?:duration|period)\s*[:\-]?\s*"
    r"(\d+\s*(?:days?|weeks?|months?|years?|hours?))",
    re.IGNORECASE,
)

NAME_LABEL_PATTERN = re.compile(
    r"(?:name|awarded\s*to|presented\s*to|this\s+is\s+to\s+certify\s+that)"
    r"[ \t]*[:\-]?[ \t\n]*([A-Z][a-zA-Z\.\'\-]+(?:[ \t]+[A-Z][a-zA-Z\.\'\-]+){0,3})",
    re.IGNORECASE,
)

TITLE_LABEL_PATTERN = re.compile(
    r"(?:course\s*(?:title)?|program(?:me)?|for\s+successfully\s+completing"
    r"|for\s+(?:active\s+participation\s+in|outstanding\s+performance\s+in)|"
    r"certificate\s+(?:title|of|in)|completed\s+the(?:\s+course)?)"
    r"[ \t]*[:\-]?[ \t\n]*([A-Za-z0-9 ,&\-]{4,60})",
    re.IGNORECASE,
)

ORG_LABEL_PATTERN = re.compile(
    r"(?:issued\s*by|organi[sz]ation|institute|academy|university|"
    r"authority)\s*[:\-]?\s*([A-Za-z0-9 &\.,\-]{3,60})",
    re.IGNORECASE,
)


def _first_match(pattern: re.Pattern, text: str) -> Optional[str]:
    match = pattern.search(text)
    if match:
        # Collapse internal newlines/whitespace (OCR often breaks a value
        # across lines) before trimming stray punctuation from the edges.
        value = re.sub(r"\s+", " ", match.group(1))
        return value.strip(" .,:-")
    return None


def _guess_title_from_layout(lines):
    """
    Heuristic fallback: certificates often have the course/achievement
    title as a short, prominent, title-cased or all-caps line somewhere
    in the first half of the document.
    """
    for line in lines[: max(1, len(lines) // 2)]:
        clean = line.strip()
        if 4 <= len(clean) <= 60 and clean.isupper() and any(c.isalpha() for c in clean):
            return clean.title()
    return None


def extract_fields(raw_text: str) -> ExtractedFields:
    """
    Main extraction function. Runs all pattern matchers against the raw
    OCR text and returns a populated ExtractedFields object. Any field
    that cannot be confidently identified is left as None so the caller
    (and the frontend) can clearly show "Not Detected" rather than a
    guess presented as fact.
    """
    text = raw_text or ""
    lines = [l for l in text.splitlines() if l.strip()]

    fields = ExtractedFields()

    fields.candidate_name = _first_match(NAME_LABEL_PATTERN, text)
    fields.certificate_title = (
        _first_match(TITLE_LABEL_PATTERN, text) or _guess_title_from_layout(lines)
    )
    fields.organization_name = _first_match(ORG_LABEL_PATTERN, text)
    fields.issue_date = _first_match(DATE_PATTERN, text)
    fields.certificate_number = (
        _first_match(CERT_NUMBER_PATTERN, text) or _first_match(GENERIC_ID_PATTERN, text)
    )
    fields.grade_score = _first_match(GRADE_PATTERN, text)
    fields.duration = _first_match(DURATION_PATTERN, text)

    return fields
