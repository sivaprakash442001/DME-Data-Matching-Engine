"""
Automatic data type detector for columns and values.
Infers type: 'email', 'phone', 'address', 'person_name', 'company', 'id_code', or 'generic_text'.
"""
import re
from typing import List, Optional, Tuple
from app.normalization.abbreviations import DEFAULT_COMPANY_ABBREVIATIONS, DEFAULT_ADDRESS_ABBREVIATIONS
from app.normalization.names import TITLES, SUFFIXES


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^(?:\+?[0-9]{1,4}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{3,5}$")
ID_CODE_REGEX = re.compile(r"^[A-Z0-9]{2,}[-_/][A-Z0-9-_/]+$|^[A-Z]{1,5}\d{3,12}$|^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def detect_single_value_type(val: str) -> str:
    """Classify the type of an individual string value."""
    if not val:
        return "generic_text"

    s = str(val).strip()
    if not s:
        return "generic_text"

    # 1. Email check
    if EMAIL_REGEX.match(s):
        return "email"

    # 2. Phone check
    # Digits count between 7 and 15 and minimal alpha characters
    digits = re.sub(r"\D", "", s)
    has_letters = bool(re.search(r"[a-zA-Z]", s))
    if not has_letters and 7 <= len(digits) <= 15:
        if PHONE_REGEX.match(s) or s.startswith("+") or "-" in s or " " in s:
            return "phone"

    # 3. ID / Code check (alphanumeric pattern, UUID, CUST-1234, etc.)
    if ID_CODE_REGEX.match(s) or (len(s) <= 24 and not " " in s and re.search(r"\d", s) and re.search(r"[a-zA-Z]", s)):
        return "id_code"

    tokens = s.lower().split()

    # 4. Company check
    # Check for corporate suffixes or words
    corp_indicators = set(DEFAULT_COMPANY_ABBREVIATIONS.keys()) | {
        "pvt", "ltd", "private", "limited", "corp", "corporation", "inc", "incorporated",
        "llc", "llp", "gmbh", "holding", "holdings", "technologies", "solutions", "enterprises",
        "industries", "associates", "group", "bank", "pharma", "motors", "logistics"
    }
    for t in tokens:
        clean_t = re.sub(r"[^\w]", "", t)
        if clean_t in corp_indicators:
            return "company"

    # 5. Address check
    # Digits plus street/locality indicators or comma-separated tokens
    address_indicators = set(DEFAULT_ADDRESS_ABBREVIATIONS.keys()) | {
        "road", "rd", "street", "st", "avenue", "ave", "lane", "ln", "nagar", "colony",
        "sector", "floor", "fl", "flat", "apt", "apartment", "building", "bldg", "block",
        "phase", "cross", "layout", "pin", "zip", "near", "opp", "opposite"
    }
    has_digit = bool(re.search(r"\d", s))
    address_word_count = sum(1 for t in tokens if re.sub(r"[^\w]", "", t) in address_indicators)

    if (has_digit and address_word_count >= 1) or address_word_count >= 2:
        return "address"

    # 6. Person Name check
    # Typically 2-4 tokens, no digits, may have title/suffix
    if not has_digit and 1 <= len(tokens) <= 4:
        clean_first = re.sub(r"[^\w]", "", tokens[0])
        if clean_first in TITLES:
            return "person_name"
        # If comma separated e.g. "Smith, John"
        if "," in s and len(tokens) <= 3:
            return "person_name"

    # Fallback heuristic for names
    if not has_digit and 2 <= len(tokens) <= 3 and all(len(t) >= 2 for t in tokens):
        return "person_name"

    return "generic_text"


def detect_column_type(samples: List[str], column_name: Optional[str] = None) -> Tuple[str, float]:
    """
    Detect the most likely type for a column given a list of sample values and the column header name.
    Returns (detected_type, confidence_score_0_to_1).
    """
    # First: Check column header name hints
    if column_name:
        col_lower = column_name.lower().replace("_", " ").replace("-", " ")
        if any(w in col_lower for w in ["email", "e-mail", "mail"]):
            return "email", 0.95
        if any(w in col_lower for w in ["phone", "mobile", "tel", "contact no", "cell"]):
            return "phone", 0.95
        if any(w in col_lower for w in ["addr", "address", "street", "residence", "location", "billing addr", "shipping addr"]):
            return "address", 0.95
        if any(w in col_lower for w in ["company", "organization", "firm", "business", "employer", "vendor"]):
            return "company", 0.90
        if any(w in col_lower for w in ["name", "full name", "first name", "last name", "customer name", "contact name", "person"]):
            return "person_name", 0.90
        if any(w in col_lower for w in ["id", "code", "uuid", "sku", "cust id", "ref", "ssn", "identifier"]):
            return "id_code", 0.90

    # Second: Sample inspection
    valid_samples = [str(x) for x in samples if x is not None and str(x).strip() and str(x).lower() != "nan"]
    if not valid_samples:
        return "generic_text", 0.5

    type_counts = {}
    for sample in valid_samples[:50]:  # inspect first 50 non-empty values
        t = detect_single_value_type(sample)
        type_counts[t] = type_counts.get(t, 0) + 1

    total = len(valid_samples[:50])
    most_common_type = max(type_counts, key=type_counts.get)
    confidence = type_counts[most_common_type] / total

    return most_common_type, round(confidence, 2)
