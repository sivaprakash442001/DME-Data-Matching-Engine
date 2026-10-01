"""
Specialized Address Matching Engine.
Parses address components (house number, street, locality, city/state, postal code)
and performs weighted component evaluation plus token-level similarity.
"""
import re
from typing import Dict, Optional
from app.normalization.addresses import AddressParser, default_address_parser
from app.normalization.cleaner import NormalizationSettings
from app.matching.algorithms import (
    levenshtein_similarity,
    jaro_winkler_similarity,
    token_set_ratio,
    token_sort_ratio,
    exact_match_score,
)
from app.scoring.weights import get_weights_for_type
from app.scoring.scorer import MatchResult, default_scorer


class AddressMatcher:
    """
    Evaluates address similarity using component-level breakdown and token alignment.
    """

    def __init__(self, parser: Optional[AddressParser] = None, scorer=None):
        self.parser = parser or default_address_parser
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

        if raw_a == raw_b and raw_a:
            weights = get_weights_for_type("address", custom_weights)
            component_scores = {
                "house_number": 100.0,
                "street": 100.0,
                "locality": 100.0,
                "city_state": 100.0,
                "postal_code": 100.0,
                "token_similarity": 100.0,
            }
            return self.scorer.build_result(
                original_a=raw_a,
                original_b=raw_b,
                normalized_a=raw_a,
                normalized_b=raw_b,
                component_scores=component_scores,
                weights=weights,
                matching_type="address",
                custom_summary="Identical address match across all components.",
            )

        # Parse components
        addr_a = self.parser.parse(raw_a)
        addr_b = self.parser.parse(raw_b)

        if addr_a.normalized == addr_b.normalized and addr_a.normalized:
            weights = get_weights_for_type("address", custom_weights)
            component_scores = {
                "house_number": 100.0,
                "street": 100.0,
                "locality": 100.0,
                "city_state": 100.0,
                "postal_code": 100.0,
                "token_similarity": 100.0,
            }
            return self.scorer.build_result(
                original_a=raw_a,
                original_b=raw_b,
                normalized_a=addr_a.normalized,
                normalized_b=addr_b.normalized,
                component_scores=component_scores,
                weights=weights,
                matching_type="address",
                custom_summary="Normalized identical address match.",
            )

        # 1. House number similarity
        # If both have numbers: exact match -> 100, different -> 0 (or slight partial if 12 vs 12-A)
        house_score = 0.0
        if addr_a.house_number and addr_b.house_number:
            if addr_a.house_number == addr_b.house_number:
                house_score = 100.0
            elif addr_a.house_number.isdigit() and addr_b.house_number.isdigit():
                # Different numbers (e.g. 100 vs 200) represent distinct properties
                house_score = 0.0
            else:
                clean_num_a = re.sub(r"\D", "", addr_a.house_number)
                clean_num_b = re.sub(r"\D", "", addr_b.house_number)
                if clean_num_a == clean_num_b and clean_num_a:
                    house_score = 80.0
                else:
                    house_score = 0.0
        elif not addr_a.house_number and not addr_b.house_number:
            # Neither has a number; neutral score
            house_score = 80.0
        else:
            # One has a number, one doesn't
            house_score = 40.0

        # 2. Street similarity
        street_score = 0.0
        if addr_a.street and addr_b.street:
            street_score = max(
                token_sort_ratio(addr_a.street, addr_b.street),
                jaro_winkler_similarity(addr_a.street, addr_b.street)
            )
        else:
            # If street wasn't parsed cleanly into its own field, compare token sets of full normalized string
            street_score = token_set_ratio(addr_a.normalized, addr_b.normalized)

        # 3. Locality similarity
        locality_score = 0.0
        if addr_a.locality and addr_b.locality:
            locality_score = token_sort_ratio(addr_a.locality, addr_b.locality)
        elif not addr_a.locality and not addr_b.locality:
            locality_score = token_sort_ratio(addr_a.normalized, addr_b.normalized)
        else:
            locality_score = 60.0 if token_set_ratio(addr_a.normalized, addr_b.normalized) > 70 else 30.0

        # 4. City and State similarity
        city_score = 100.0 if (addr_a.city and addr_b.city and addr_a.city == addr_b.city) else 0.0
        if not addr_a.city or not addr_b.city:
            # Check if one city appears in the other's normalized string
            if addr_a.city and addr_a.city in addr_b.normalized:
                city_score = 100.0
            elif addr_b.city and addr_b.city in addr_a.normalized:
                city_score = 100.0
            else:
                city_score = 50.0  # neutral if city unknown

        state_score = 100.0 if (addr_a.state and addr_b.state and addr_a.state == addr_b.state) else 0.0
        if not addr_a.state or not addr_b.state:
            state_score = 50.0

        city_state_score = (city_score * 0.6) + (state_score * 0.4)

        # 5. Postal code similarity
        postal_score = 0.0
        if addr_a.postal_code and addr_b.postal_code:
            postal_score = 100.0 if addr_a.postal_code == addr_b.postal_code else 0.0
        elif not addr_a.postal_code and not addr_b.postal_code:
            # Neutral if neither provided
            postal_score = 75.0
        else:
            # One provided, one missing
            postal_score = 50.0

        # 6. Overall token similarity (Token Set / Sort ratio)
        token_sim = (token_sort_ratio(addr_a.normalized, addr_b.normalized) * 0.5) + \
                    (token_set_ratio(addr_a.normalized, addr_b.normalized) * 0.5)

        component_scores = {
            "house_number": house_score,
            "street": street_score,
            "locality": locality_score,
            "city_state": city_state_score,
            "postal_code": postal_score,
            "token_similarity": token_sim,
        }

        # House number conflict check (e.g. 100 Main Street vs 200 Main Street)
        if addr_a.house_number and addr_b.house_number and house_score == 0.0:
            # Different house numbers mean different buildings on the street
            component_scores["house_number"] = 0.0
            component_scores["locality"] = min(locality_score, 40.0)
            component_scores["postal_code"] = min(postal_score, 40.0)
            component_scores["city_state"] = min(city_state_score, 40.0)
            component_scores["token_similarity"] = min(token_sim, 50.0)

        # Geographic mismatch check (e.g. Chennai, Tamil Nadu vs Mumbai, Maharashtra)
        has_geo_a = bool(addr_a.city or addr_a.state)
        has_geo_b = bool(addr_b.city or addr_b.state)
        if has_geo_a and has_geo_b and city_score == 0.0 and state_score == 0.0:
            component_scores["house_number"] = 0.0
            component_scores["street"] = 0.0
            component_scores["locality"] = 0.0
            component_scores["postal_code"] = 0.0
            component_scores["city_state"] = 0.0
            component_scores["token_similarity"] = min(token_sim, 25.0)

        weights = get_weights_for_type("address", custom_weights)

        summary_parts = []
        if postal_score == 100.0 and addr_a.postal_code:
            summary_parts.append(f"Postal code match ({addr_a.postal_code})")
        if addr_a.city and addr_b.city and addr_a.city == addr_b.city:
            summary_parts.append(f"City match ({addr_a.city.title()})")
        if house_score == 100.0 and addr_a.house_number:
            summary_parts.append(f"House/unit match (#{addr_a.house_number})")
        elif house_score == 0.0 and addr_a.house_number and addr_b.house_number:
            summary_parts.append(f"Different house numbers ({addr_a.house_number} vs {addr_b.house_number})")

        custom_summary = "; ".join(summary_parts) if summary_parts else None

        return self.scorer.build_result(
            original_a=raw_a,
            original_b=raw_b,
            normalized_a=addr_a.normalized,
            normalized_b=addr_b.normalized,
            component_scores=component_scores,
            weights=weights,
            matching_type="address",
            custom_summary=custom_summary,
        )


default_address_matcher = AddressMatcher()
