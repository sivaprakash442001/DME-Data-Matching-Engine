"""
Specialized Phone Number Matching Engine.
Normalizes country codes, leading zeros, extensions, hyphens, brackets,
and compares national subscriber numbers.
"""
import re
from typing import Dict, Optional, Tuple
from app.normalization.cleaner import NormalizationSettings
from app.matching.algorithms import levenshtein_similarity
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class PhoneMatcher:
    """
    Evaluates phone number equivalence accounting for international prefixes and formatting.
    """

    def __init__(self, scorer=None):
        self.scorer = scorer or default_scorer

    def parse_phone(self, phone_str: str) -> Tuple[str, str, str]:
        """
        Extract (country_code, national_number, extension).
        """
        raw = str(phone_str or "").strip()
        if not raw:
            return "", "", ""

        # Extract extension if any: e.g. ext. 123, x45
        ext_match = re.search(r"(?i)\b(?:ext\.?|x)\s*([0-9]+)\b", raw)
        extension = ext_match.group(1) if ext_match else ""
        clean_raw = re.sub(r"(?i)\b(?:ext\.?|x)\s*([0-9]+)\b", "", raw)

        # Extract only digits and leading plus
        has_plus = clean_raw.strip().startswith("+")
        digits = re.sub(r"\D", "", clean_raw)

        if not digits:
            return "", "", extension

        country_code = ""
        national_number = digits

        # Standard Country Code Heuristics
        # If starts with 00 (international call prefix), treat as +
        if digits.startswith("00") and len(digits) > 10:
            digits = digits[2:]
            has_plus = True

        if has_plus:
            # Common country codes: +91 (2 digits), +1 (1 digit), +44 (2 digits), +61 (2 digits)
            if digits.startswith("1") and len(digits) == 11:
                country_code = "1"
                national_number = digits[1:]
            elif digits.startswith("91") and len(digits) == 12:
                country_code = "91"
                national_number = digits[2:]
            elif digits.startswith("44") and len(digits) in (12, 13):
                country_code = "44"
                national_number = digits[2:]
            else:
                # Default to last 10 digits as national number if longer
                if len(digits) > 10:
                    country_code = digits[:-10]
                    national_number = digits[-10:]
        else:
            # Check leading 0 (trunk prefix in India, UK, etc.)
            if digits.startswith("0") and len(digits) == 11:
                national_number = digits[1:]
            elif len(digits) > 10:
                # Possibly country code included without plus
                if digits.startswith("91") and len(digits) == 12:
                    country_code = "91"
                    national_number = digits[2:]
                elif digits.startswith("1") and len(digits) == 11:
                    country_code = "1"
                    national_number = digits[1:]

        return country_code, national_number, extension

    def match(
        self,
        str_a: str,
        str_b: str,
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        raw_a = str(str_a or "").strip()
        raw_b = str(str_b or "").strip()

        cc_a, nat_a, ext_a = self.parse_phone(raw_a)
        cc_b, nat_b, ext_b = self.parse_phone(raw_b)

        # 1. National digits match
        if nat_a and nat_b:
            if nat_a == nat_b:
                digits_score = 100.0
            else:
                # Compare last 10 digits if lengths differ
                min_len = min(len(nat_a), len(nat_b))
                if min_len >= 7 and nat_a[-min_len:] == nat_b[-min_len:]:
                    digits_score = 90.0
                else:
                    digits_score = levenshtein_similarity(nat_a, nat_b)
        else:
            digits_score = 0.0

        # 2. Country code match
        if cc_a and cc_b:
            country_score = 100.0 if cc_a == cc_b else 0.0
        elif not cc_a and not cc_b:
            country_score = 90.0  # neither specified
        else:
            country_score = 85.0  # one specified, one omitted

        # 3. Overall digit edit distance
        edit_score = levenshtein_similarity(re.sub(r"\D", "", raw_a), re.sub(r"\D", "", raw_b))

        component_scores = {
            "digits_match": digits_score,
            "country_code": country_score,
            "edit_distance": edit_score,
        }

        weights = get_weights_for_type("phone", custom_weights)

        summary_parts = []
        if digits_score == 100.0:
            summary_parts.append(f"Identical national number ({nat_a})")
        if cc_a and cc_b and cc_a == cc_b:
            summary_parts.append(f"Matching country code (+{cc_a})")
        elif cc_a and cc_b and cc_a != cc_b:
            summary_parts.append(f"Different country codes (+{cc_a} vs +{cc_b})")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        norm_a = f"+{cc_a} {nat_a}".strip() if cc_a else nat_a
        norm_b = f"+{cc_b} {nat_b}".strip() if cc_b else nat_b

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=norm_a,
            normalized_b=norm_b,
            component_scores=component_scores,
            weights=weights,
            matching_type="phone",
            custom_summary=custom_summary,
        )


default_phone_matcher = PhoneMatcher()
