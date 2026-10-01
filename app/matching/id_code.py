"""
Specialized ID / Code Matching Engine.
Handles alphanumeric identifiers, SKUs, customer IDs, and reference numbers.
"""
import re
from typing import Dict, Optional, Tuple
from app.normalization.cleaner import NormalizationSettings
from app.matching.algorithms import levenshtein_similarity
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class IdCodeMatcher:
    """
    Evaluates identifiers and codes with high strictness on alphanumeric tokens.
    """

    def __init__(self, scorer=None):
        self.scorer = scorer or default_scorer

    def split_id(self, code: str) -> Tuple[str, str, str]:
        """
        Normalize identifier into clean alphanumeric, prefix letters, and trailing numbers.
        e.g. "CUST-0042A" -> ("cust0042a", "cust", "0042")
        """
        clean = re.sub(r"[^a-zA-Z0-9]", "", code).lower()
        prefix_match = re.match(r"^([a-zA-Z]+)", clean)
        num_match = re.search(r"([0-9]+)", clean)

        prefix = prefix_match.group(1) if prefix_match else ""
        num = num_match.group(1) if num_match else ""
        return clean, prefix, num

    def match(
        self,
        str_a: str,
        str_b: str,
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        raw_a = str(str_a or "").strip()
        raw_b = str(str_b or "").strip()

        clean_a, prefix_a, num_a = self.split_id(raw_a)
        clean_b, prefix_b, num_b = self.split_id(raw_b)

        # 1. Exact clean alphanumeric match
        exact_clean = 100.0 if clean_a == clean_b and clean_a else 0.0

        # 2. Prefix match
        if prefix_a and prefix_b:
            prefix_score = 100.0 if prefix_a == prefix_b else 0.0
        elif not prefix_a and not prefix_b:
            prefix_score = 100.0
        else:
            prefix_score = 50.0

        # 3. Numeric sequence match (e.g. leading zero tolerance 0042 vs 42)
        if num_a and num_b:
            if num_a == num_b or int(num_a) == int(num_b):
                num_score = 100.0
            else:
                num_score = 0.0
        elif not num_a and not num_b:
            num_score = 100.0
        else:
            num_score = 40.0

        # 4. Levenshtein on clean string
        lev_score = levenshtein_similarity(clean_a, clean_b)

        component_scores = {
            "exact_clean": exact_clean,
            "prefix_match": prefix_score,
            "levenshtein": lev_score,
        }

        weights = get_weights_for_type("id_code", custom_weights)

        summary_parts = []
        if exact_clean == 100.0:
            summary_parts.append(f"Exact identifier match ({clean_a.upper()})")
        elif prefix_score == 100.0 and prefix_a:
            summary_parts.append(f"Matching prefix '{prefix_a.upper()}'")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=clean_a,
            normalized_b=clean_b,
            component_scores=component_scores,
            weights=weights,
            matching_type="id_code",
            custom_summary=custom_summary,
        )


default_id_code_matcher = IdCodeMatcher()
