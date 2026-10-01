"""
Generic text matching engine.
Applies a composite of string distance, token set/sort, Jaro-Winkler, and partial substring algorithms.
"""
from typing import Dict, Optional
from app.normalization.cleaner import default_normalizer, NormalizationSettings
from app.matching.algorithms import (
    exact_match_score,
    levenshtein_similarity,
    jaro_winkler_similarity,
    token_sort_ratio,
    token_set_ratio,
    partial_ratio,
)
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class GenericTextMatcher:
    """
    Evaluates generic unstructured text across multiple similarity metrics.
    """

    def __init__(self, normalizer=None, scorer=None):
        self.normalizer = normalizer or default_normalizer
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

        # Normalize strings
        norm_a = self.normalizer.normalize(raw_a, settings)
        norm_b = self.normalizer.normalize(raw_b, settings)

        # Compute individual algorithm components
        exact_norm = exact_match_score(norm_a, norm_b)
        token_sort = token_sort_ratio(norm_a, norm_b)
        token_set = token_set_ratio(norm_a, norm_b)
        jw = jaro_winkler_similarity(norm_a, norm_b)
        lev = levenshtein_similarity(norm_a, norm_b)
        partial = partial_ratio(norm_a, norm_b)

        component_scores = {
            "exact_normalized": exact_norm,
            "token_sort": token_sort,
            "token_set": token_set,
            "jaro_winkler": jw,
            "levenshtein": lev,
            "partial_match": partial,
        }

        weights = get_weights_for_type("generic_text", custom_weights)

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=norm_a,
            normalized_b=norm_b,
            component_scores=component_scores,
            weights=weights,
            matching_type="generic_text",
        )


default_generic_matcher = GenericTextMatcher()
