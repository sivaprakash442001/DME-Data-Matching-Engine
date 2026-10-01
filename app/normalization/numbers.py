"""
Number normalization module.
Handles variations of number prefixes, ordinals, floors, apartment/unit indicators, and word numbers.
"""
import re


WORD_TO_NUMBER = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "first": "1st",
    "second": "2nd",
    "third": "3rd",
    "fourth": "4th",
    "fifth": "5th",
    "sixth": "6th",
    "seventh": "7th",
    "eighth": "8th",
    "ninth": "9th",
    "tenth": "10th",
}


def normalize_number_expressions(text: str) -> str:
    """
    Standardize number prefixes (#25, No. 25, Number 25 -> no 25),
    floor designations (1st floor, floor 1, f1, fl 1 -> floor 1),
    and ordinal expressions.
    """
    if not text:
        return ""

    result = text

    # Standardize "No.", "No:", "Number", "#" followed by digits
    # e.g., "# 25" or "#25" or "No. 25" or "Number 25" -> "number 25"
    result = re.sub(r"(?i)\b(?:no\.?|num\.?|number|#)\s*([0-9]+[a-z]?)\b", r"number \1", result)
    result = re.sub(r"#\s*([0-9]+[a-z]?)", r"number \1", result)

    # Standardize Floor representations:
    # "1st floor", "first floor", "floor 1", "fl 1", "fl. 1", "f-1", "f 1" -> "floor 1"
    result = re.sub(r"(?i)\b(1st|first)\s+(?:flr|fl\.?|floor)\b", "floor 1", result)
    result = re.sub(r"(?i)\b(2nd|second)\s+(?:flr|fl\.?|floor)\b", "floor 2", result)
    result = re.sub(r"(?i)\b(3rd|third)\s+(?:flr|fl\.?|floor)\b", "floor 3", result)
    result = re.sub(r"(?i)\b([0-9]+)(?:st|nd|rd|th)?\s+(?:flr|fl\.?|floor)\b", r"floor \1", result)
    result = re.sub(r"(?i)\b(?:flr|fl\.?|floor)\s*[:\-#]?\s*([0-9]+)\b", r"floor \1", result)
    result = re.sub(r"(?i)\bf[\-\s]?([0-9]+)\b", r"floor \1", result)

    # Standardize Ground Floor / Basement
    result = re.sub(r"(?i)\b(?:g[\-\s]?flr|g[\-\s]?fl\.?|ground\s+floor|gf)\b", "ground floor", result)
    result = re.sub(r"(?i)\b(?:b[\-\s]?flr|b[\-\s]?fl\.?|basement|b1)\b", "basement", result)

    # Standardize Apartment/Suite/Flat
    result = re.sub(r"(?i)\b(?:apt|apartment|flat|ste|suite|unit)\s*[:\-#]?\s*([0-9a-z\-]+)\b", r"flat \1", result)

    # Standardize simple word numbers when isolated (e.g., "sector three" -> "sector 3")
    for word, num in WORD_TO_NUMBER.items():
        result = re.sub(rf"(?i)\b{word}\b", num, result)

    return result


def extract_numbers(text: str) -> list[str]:
    """Extract all distinct numeric tokens from text."""
    if not text:
        return []
    return re.findall(r"\b\d+\b", text)
