"""
Master Matching Engine.
Coordinates specialized matchers, automatic type detection, multi-column matching,
and batch processing over datasets.
"""
from typing import Dict, List, Optional, Any, Callable
import pandas as pd

from app.normalization.cleaner import NormalizationSettings, default_normalizer
from app.normalization.abbreviations import AbbreviationManager
from app.matching.detector import detect_column_type, detect_single_value_type
from app.matching.generic import GenericTextMatcher, default_generic_matcher
from app.matching.address import AddressMatcher, default_address_matcher
from app.matching.name import PersonNameMatcher, default_name_matcher
from app.matching.company import CompanyNameMatcher, default_company_matcher
from app.matching.email import EmailMatcher, default_email_matcher
from app.matching.phone import PhoneMatcher, default_phone_matcher
from app.matching.id_code import IdCodeMatcher, default_id_code_matcher
from app.scoring.scorer import MatchResult, MatchScorer, MatchThresholds, default_scorer


class MatchingEngine:
    """
    Central matching engine orchestrating all data types and algorithms.
    """

    def __init__(
        self,
        scorer: Optional[MatchScorer] = None,
        abbrev_manager: Optional[AbbreviationManager] = None,
    ):
        self.scorer = scorer or default_scorer
        self.abbrev_manager = abbrev_manager

        # Initialize matchers
        self.generic_matcher = GenericTextMatcher(scorer=self.scorer)
        self.address_matcher = default_address_matcher
        self.name_matcher = default_name_matcher
        self.company_matcher = default_company_matcher
        self.email_matcher = default_email_matcher
        self.phone_matcher = default_phone_matcher
        self.id_code_matcher = default_id_code_matcher

        self.matchers = {
            "generic_text": self.generic_matcher,
            "address": self.address_matcher,
            "person_name": self.name_matcher,
            "company": self.company_matcher,
            "email": self.email_matcher,
            "phone": self.phone_matcher,
            "id_code": self.id_code_matcher,
        }

    def get_matcher(self, matching_type: str):
        key = matching_type.lower()
        return self.matchers.get(key, self.generic_matcher)

    def match_pair(
        self,
        val_a: Any,
        val_b: Any,
        matching_type: str = "auto",
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> MatchResult:
        """
        Match two single values. If matching_type is 'auto', detect type automatically.
        """
        str_a = "" if pd.isna(val_a) else str(val_a).strip()
        str_b = "" if pd.isna(val_b) else str(val_b).strip()

        # Handle empty cases
        if not str_a and not str_b:
            return self.scorer.build_result(
                original_a=str_a,
                original_b=str_b,
                normalized_a="",
                normalized_b="",
                component_scores={"exact": 100.0},
                weights={"exact": 100.0},
                matching_type="generic_text",
                custom_summary="Both values are empty.",
            )
        if not str_a or not str_b:
            return self.scorer.build_result(
                original_a=str_a,
                original_b=str_b,
                normalized_a=str_a,
                normalized_b=str_b,
                component_scores={"exact": 0.0},
                weights={"exact": 100.0},
                matching_type="generic_text",
                custom_summary="One value is missing.",
            )

        resolved_type = matching_type.lower()
        if resolved_type in ("auto", "auto_detect", "autodetect"):
            # Detect based on values
            type_a = detect_single_value_type(str_a)
            type_b = detect_single_value_type(str_b)
            # If both agree, use that; else if one detected something specific, prefer that
            if type_a == type_b:
                resolved_type = type_a
            elif type_a != "generic_text":
                resolved_type = type_a
            elif type_b != "generic_text":
                resolved_type = type_b
            else:
                resolved_type = "generic_text"

        matcher = self.get_matcher(resolved_type)
        return matcher.match(
            str_a=str_a,
            str_b=str_b,
            settings=settings,
            custom_weights=custom_weights,
        )

    def match_dataframe(
        self,
        df: pd.DataFrame,
        col_a: str,
        col_b: str,
        matching_type: str = "auto",
        settings: Optional[NormalizationSettings] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[MatchResult]:
        """
        Process a DataFrame pairwise between col_a and col_b.
        """
        total = len(df)
        results: List[MatchResult] = []

        # If matching_type is 'auto', detect type at column level first for consistency and speed
        detected_col_type = "generic_text"
        if matching_type in ("auto", "auto_detect"):
            samples = list(df[col_a].dropna().astype(str).head(30)) + list(df[col_b].dropna().astype(str).head(30))
            detected_col_type, _ = detect_column_type(samples, col_a)

        for idx, row in df.iterrows():
            val_a = row.get(col_a, "")
            val_b = row.get(col_b, "")

            # Use detected column type if auto
            active_type = detected_col_type if matching_type in ("auto", "auto_detect") else matching_type
            result = self.match_pair(
                val_a=val_a,
                val_b=val_b,
                matching_type=active_type,
                settings=settings,
                custom_weights=custom_weights,
            )
            results.append(result)

            update_interval = max(1, min(50, total // 100)) if total > 0 else 1
            if progress_callback and (idx % update_interval == 0 or idx == total - 1):
                progress_callback(idx + 1, total)

        return results

    def match_multi_column(
        self,
        df: pd.DataFrame,
        column_configs: List[Dict[str, Any]],  # list of {col_a, col_b, type, weight}
        settings: Optional[NormalizationSettings] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[MatchResult]:
        """
        Match across multiple column pairs (e.g. First Name + Last Name + City)
        and compute a weighted overall score.
        """
        total = len(df)
        final_results: List[MatchResult] = []

        # Normalize column weights
        total_weight = sum(c.get("weight", 1.0) for c in column_configs)
        norm_configs = []
        for c in column_configs:
            w = c.get("weight", 1.0)
            norm_configs.append({
                "col_a": c["col_a"],
                "col_b": c["col_b"],
                "type": c.get("type", "auto"),
                "weight": (w / total_weight) * 100.0 if total_weight > 0 else 100.0 / len(column_configs),
            })

        for idx, row in df.iterrows():
            composite_score = 0.0
            component_scores = {}
            explanations = []
            matching_tokens = set()
            norm_a_parts = []
            norm_b_parts = []
            raw_a_parts = []
            raw_b_parts = []

            for cfg in norm_configs:
                col_a = cfg["col_a"]
                col_b = cfg["col_b"]
                w = cfg["weight"]
                m_type = cfg["type"]

                sub_res = self.match_pair(
                    val_a=row.get(col_a, ""),
                    val_b=row.get(col_b, ""),
                    matching_type=m_type,
                    settings=settings,
                )

                field_label = f"{col_a} ↔ {col_b}"
                component_scores[field_label] = sub_res.score
                composite_score += sub_res.score * (w / 100.0)
                matching_tokens.update(sub_res.explanation.matching_tokens)

                raw_a_parts.append(f"{col_a}: {sub_res.explanation.original_a}")
                raw_b_parts.append(f"{col_b}: {sub_res.explanation.original_b}")
                norm_a_parts.append(sub_res.explanation.normalized_a)
                norm_b_parts.append(sub_res.explanation.normalized_b)
                explanations.append(f"{field_label} ({round(sub_res.score, 1)}%)")

            final_score = max(0.0, min(100.0, composite_score))
            status = self.scorer.determine_status(final_score)
            confidence = self.scorer.determine_confidence(final_score, component_scores)

            explanation = self.scorer.build_result(
                original_a=" | ".join(raw_a_parts),
                original_b=" | ".join(raw_b_parts),
                normalized_a=" | ".join(norm_a_parts),
                normalized_b=" | ".join(norm_b_parts),
                component_scores=component_scores,
                weights={f"{c['col_a']} ↔ {c['col_b']}": c["weight"] for c in norm_configs},
                matching_type="multi_column",
                custom_summary="; ".join(explanations),
            )
            final_results.append(explanation)

            update_interval = max(1, min(50, total // 100)) if total > 0 else 1
            if progress_callback and (idx % update_interval == 0 or idx == total - 1):
                progress_callback(idx + 1, total)

        return final_results


default_engine = MatchingEngine()
