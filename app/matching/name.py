"""
Specialized Person Name Matching Engine.
Handles inverted names ("Smith, John"), middle names, initials ("John A Smith" vs "John Albert Smith"),
honorifics, and token reordering.
"""
from typing import Dict, Optional
from app.normalization.names import PersonNameParser, default_name_parser
from app.normalization.cleaner import NormalizationSettings
from app.matching.algorithms import (
    jaro_winkler_similarity,
    levenshtein_similarity,
    token_sort_ratio,
    token_set_ratio,
)
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class PersonNameMatcher:
    """
    Evaluates person name similarity with awareness of name structure and initials.
    """

    def __init__(self, parser: Optional[PersonNameParser] = None, scorer=None):
        self.parser = parser or default_name_parser
        self.scorer = scorer or default_scorer

    def match(
        self,
        str_a: str,
        str_b: str,
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        raw_a = str(str_a or "").strip()
        raw_b = str(str_b or "").strip()

        parsed_a = self.parser.parse(raw_a)
        parsed_b = self.parser.parse(raw_b)

        # 1. First name similarity
        fn_a = (parsed_a.first_name or "").lower()
        fn_b = (parsed_b.first_name or "").lower()
        ln_a = (parsed_a.last_name or "").lower()
        ln_b = (parsed_b.last_name or "").lower()

        # Check inverted order e.g. "Smith John" vs "John Smith"
        if fn_a and ln_a and fn_b and ln_b and fn_a == ln_b and ln_a == fn_b:
            first_score = 100.0
            last_score = 100.0
        else:
            # 1. First name similarity
            if fn_a and fn_b:
                if fn_a == fn_b:
                    first_score = 100.0
                elif (len(fn_a) == 1 and fn_b.startswith(fn_a)) or (len(fn_b) == 1 and fn_a.startswith(fn_b)):
                    # One is an initial of the other: "J" vs "John"
                    first_score = 92.0
                elif fn_a == ln_b:
                    first_score = 95.0
                else:
                    first_score = jaro_winkler_similarity(fn_a, fn_b)
            else:
                first_score = 70.0

            # 2. Last name similarity
            if ln_a and ln_b:
                if ln_a == ln_b:
                    last_score = 100.0
                elif ln_a == fn_b:
                    last_score = 95.0
                else:
                    last_score = jaro_winkler_similarity(ln_a, ln_b)
            elif not ln_a and not ln_b:
                last_score = first_score
            else:
                # Check if last name appears anywhere in the other string
                if ln_a and ln_a in parsed_b.normalized:
                    last_score = 95.0
                elif ln_b and ln_b in parsed_a.normalized:
                    last_score = 95.0
                else:
                    last_score = 40.0

        # 3. Token order / Sort ratio
        # Captures "John Smith" vs "Smith John" seamlessly
        order_score = max(
            token_sort_ratio(parsed_a.normalized, parsed_b.normalized),
            token_set_ratio(parsed_a.normalized, parsed_b.normalized)
        )

        # 4. Initials similarity
        in_a = parsed_a.initials
        in_b = parsed_b.initials
        if in_a and in_b:
            if in_a == in_b:
                initials_score = 100.0
            elif in_a[0] == in_b[0] and (len(in_a) == 1 or len(in_b) == 1 or in_a[-1] == in_b[-1]):
                # First initial and last initial match
                initials_score = 90.0
            else:
                # Intersect initials
                common = set(in_a).intersection(set(in_b))
                initials_score = (len(common) / max(len(in_a), len(in_b))) * 100.0
        else:
            initials_score = 75.0

        component_scores = {
            "first_name": first_score,
            "last_name": last_score,
            "token_order_sort": order_score,
            "initials": initials_score,
        }

        weights = get_weights_for_type("person_name", custom_weights)

        summary_parts = []
        if fn_a == fn_b and fn_a:
            summary_parts.append(f"First name match ({fn_a.title()})")
        if ln_a == ln_b and ln_a:
            summary_parts.append(f"Last name match ({ln_a.title()})")
        if order_score >= 95.0 and raw_a.lower() != raw_b.lower():
            summary_parts.append("Order inversion accounted for")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=parsed_a.normalized,
            normalized_b=parsed_b.normalized,
            component_scores=component_scores,
            weights=weights,
            matching_type="person_name",
            custom_summary=custom_summary,
        )


default_name_matcher = PersonNameMatcher()
