"""
Specialized Email Matching Engine.
Separates local part and domain, enforces strict domain validation,
and applies conservative scoring for structural variations (e.g. dots or aliases).
"""
import re
from typing import Dict, Optional, Tuple
from app.normalization.cleaner import NormalizationSettings
from app.matching.algorithms import (
    levenshtein_similarity,
    jaro_winkler_similarity,
    exact_match_score,
)
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class EmailMatcher:
    """
    Evaluates email similarity with domain verification and conservative local-part comparison.
    """

    def __init__(self, scorer=None):
        self.scorer = scorer or default_scorer

    def split_email(self, email: str) -> Tuple[str, str]:
        """Split email into clean (local_part, domain)."""
        clean = email.strip().lower()
        if "@" in clean:
            parts = clean.split("@", 1)
            return parts[0].strip(), parts[1].strip()
        return clean, ""

    def match(
        self,
        str_a: str,
        str_b: str,
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        raw_a = str(str_a or "").strip()
        raw_b = str(str_b or "").strip()

        norm_a = raw_a.lower()
        norm_b = raw_b.lower()

        local_a, domain_a = self.split_email(norm_a)
        local_b, domain_b = self.split_email(norm_b)

        # 1. Exact match
        exact_score = 100.0 if norm_a == norm_b else 0.0

        # 2. Domain similarity
        if domain_a and domain_b:
            if domain_a == domain_b:
                domain_score = 100.0
            else:
                # Typo in domain e.g. "gmial.com" vs "gmail.com"
                domain_score = levenshtein_similarity(domain_a, domain_b)
                # If domains completely disagree (e.g. gmail.com vs yahoo.com), set to 0
                if domain_score < 75.0:
                    domain_score = 0.0
        elif not domain_a and not domain_b:
            domain_score = 50.0
        else:
            domain_score = 0.0

        # 3. Local part similarity
        if local_a == local_b:
            local_score = 100.0
        else:
            # Check dot variation: e.g. "john.smith" vs "johnsmith"
            no_dots_a = local_a.replace(".", "")
            no_dots_b = local_b.replace(".", "")
            if no_dots_a == no_dots_b:
                # Dot variation: conservative 88%
                local_score = 88.0
            else:
                # Check plus-addressing (e.g. "john+news" vs "john")
                base_a = local_a.split("+")[0]
                base_b = local_b.split("+")[0]
                if base_a == base_b:
                    local_score = 92.0
                else:
                    local_score = min(
                        jaro_winkler_similarity(local_a, local_b),
                        levenshtein_similarity(local_a, local_b)
                    )

        # Domain mismatch penalty: if domains are completely different, the emails cannot be the same entity!
        if domain_score == 0.0 and domain_a and domain_b:
            local_score = min(local_score, 15.0)

        component_scores = {
            "domain": domain_score,
            "local_part": local_score,
            "exact_match": exact_score,
        }

        weights = get_weights_for_type("email", custom_weights)

        summary_parts = []
        if exact_score == 100.0:
            summary_parts.append("Exact email address match")
        elif domain_score == 100.0:
            summary_parts.append(f"Matching domain (@{domain_a})")
            if local_a.replace(".", "") == local_b.replace(".", ""):
                summary_parts.append("Dot placement variation in username")
        elif domain_score == 0.0 and domain_a and domain_b:
            summary_parts.append(f"Mismatched domains ({domain_a} vs {domain_b})")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=norm_a,
            normalized_b=norm_b,
            component_scores=component_scores,
            weights=weights,
            matching_type="email",
            custom_summary=custom_summary,
        )


default_email_matcher = EmailMatcher()
