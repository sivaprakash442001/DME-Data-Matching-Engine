"""
Specialized Company Name Matching Engine.
Standardizes corporate legal structures (Pvt Ltd, LLC, Inc, Corp, LLP),
isolates core brand names, and matches acronyms and variants.
"""
import re
from typing import Dict, Optional, Tuple
from app.normalization.cleaner import default_normalizer, NormalizationSettings
from app.normalization.abbreviations import DEFAULT_COMPANY_ABBREVIATIONS
from app.matching.algorithms import (
    jaro_winkler_similarity,
    levenshtein_similarity,
    token_set_ratio,
    token_sort_ratio,
    exact_match_score,
)
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


LEGAL_SUFFIX_PATTERNS = [
    r"\bprivate\s+limited\b",
    r"\bpvt\s+ltd\b",
    r"\bpublic\s+limited\s+company\b",
    r"\bplc\b",
    r"\bllp\b",
    r"\bllc\b",
    r"\bltd\b",
    r"\bco\s+ltd\b",
    r"\bcorp\b",
    r"\bcorporation\b",
    r"\binc\b",
    r"\bincorporated\b",
    r"\bgmbh\b",
    r"\bsa\b",
    r"\bag\b",
    r"\bcompany\b",
    r"\bco\b",
]


class CompanyNameMatcher:
    """
    Evaluates company name similarity by stripping corporate designators to match core brand names.
    """

    def __init__(self, normalizer=None, scorer=None):
        self.normalizer = normalizer or default_normalizer
        self.scorer = scorer or default_scorer
        self.settings = NormalizationSettings(
            mode="standard",
            case_sensitive=False,
            remove_punctuation=True,
            normalize_whitespace=True,
            expand_abbreviations=True,
            normalize_numbers=True,
            category="company",
        )

    def extract_core_and_suffix(self, text: str) -> Tuple[str, str]:
        """
        Extract the core brand name and the canonical legal suffix.
        e.g. "ABC Pvt. Ltd." -> ("abc", "private limited")
        """
        # First normalize abbreviations
        norm = self.normalizer.normalize(text, self.settings)

        detected_suffix = ""
        core = norm

        # Remove dots between initials: e.g., "a b c" or "a.b.c." -> "abc"
        # If words are single letters separated by space: "a b c" -> "abc"
        tokens = core.split()
        if len(tokens) > 1 and all(len(t) == 1 for t in tokens):
            core = "".join(tokens)

        # Check for corporate suffix at end or within
        for pattern in LEGAL_SUFFIX_PATTERNS:
            match = re.search(pattern, core, re.IGNORECASE)
            if match:
                detected_suffix = match.group(0).strip()
                core = re.sub(pattern, "", core, flags=re.IGNORECASE).strip()
                break

        # Re-collapse whitespace
        core = re.sub(r"\s+", " ", core).strip()
        return core, detected_suffix

    def match(
        self,
        str_a: str,
        str_b: str,
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        raw_a = str(str_a or "").strip()
        raw_b = str(str_b or "").strip()

        core_a, suffix_a = self.extract_core_and_suffix(raw_a)
        core_b, suffix_b = self.extract_core_and_suffix(raw_b)

        norm_a = self.normalizer.normalize(raw_a, settings or self.settings)
        norm_b = self.normalizer.normalize(raw_b, settings or self.settings)

        # 1. Core Brand similarity
        if not core_a and not core_b:
            core_score = 100.0
        elif not core_a or not core_b:
            core_score = 0.0
        else:
            # Check acronym equivalence (e.g. "abc" vs "a b c" or "ibm" vs "i b m")
            clean_a_no_space = core_a.replace(" ", "")
            clean_b_no_space = core_b.replace(" ", "")
            if clean_a_no_space == clean_b_no_space:
                core_score = 100.0
            else:
                core_score = max(
                    jaro_winkler_similarity(core_a, core_b),
                    token_sort_ratio(core_a, core_b),
                    levenshtein_similarity(core_a, core_b)
                )

        # 2. Corporate Suffix match
        if suffix_a and suffix_b:
            # Check if canonicalized to same or both are private/limited variants
            if suffix_a == suffix_b:
                suffix_score = 100.0
            elif ("private" in suffix_a and "private" in suffix_b) or ("limited" in suffix_a and "limited" in suffix_b):
                suffix_score = 90.0
            else:
                suffix_score = 50.0  # Different entity type e.g. LLC vs Inc
        elif not suffix_a and not suffix_b:
            suffix_score = 85.0  # Neither has suffix
        else:
            suffix_score = 70.0  # One has suffix, one omitted it

        # 3. Token set ratio on full normalized string
        token_set = token_set_ratio(norm_a, norm_b)

        # 4. Jaro-Winkler on normalized string
        jw = jaro_winkler_similarity(norm_a, norm_b)

        component_scores = {
            "core_brand": core_score,
            "corporate_suffix": suffix_score,
            "token_set": token_set,
            "jaro_winkler": jw,
        }

        weights = get_weights_for_type("company", custom_weights)

        summary_parts = []
        if core_score >= 95.0 and core_a:
            summary_parts.append(f"Identical core entity ('{core_a}')")
        if suffix_a and suffix_b and suffix_score >= 90:
            summary_parts.append("Equivalent corporate suffixes")
        elif suffix_a != suffix_b and (suffix_a or suffix_b):
            summary_parts.append("Suffix variation accounted for")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=norm_a,
            normalized_b=norm_b,
            component_scores=component_scores,
            weights=weights,
            matching_type="company",
            custom_summary=custom_summary,
        )


default_company_matcher = CompanyNameMatcher()
