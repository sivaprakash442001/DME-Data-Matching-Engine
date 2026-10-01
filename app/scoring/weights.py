"""
Weight configurations for different matching types.
Fully customizable and validated to sum to 100%.
"""
from typing import Dict, Any


DEFAULT_WEIGHT_PROFILES: Dict[str, Dict[str, float]] = {
    "generic_text": {
        "exact_normalized": 20.0,
        "token_sort": 20.0,
        "token_set": 15.0,
        "jaro_winkler": 20.0,
        "levenshtein": 15.0,
        "partial_match": 10.0,
    },
    "address": {
        "house_number": 20.0,
        "street": 20.0,
        "locality": 15.0,
        "city_state": 15.0,
        "postal_code": 15.0,
        "token_similarity": 15.0,
    },
    "person_name": {
        "first_name": 25.0,
        "last_name": 35.0,
        "token_order_sort": 25.0,
        "initials": 15.0,
    },
    "company": {
        "core_brand": 45.0,
        "corporate_suffix": 15.0,
        "token_set": 20.0,
        "jaro_winkler": 20.0,
    },
    "email": {
        "domain": 40.0,
        "local_part": 50.0,
        "exact_match": 10.0,
    },
    "phone": {
        "digits_match": 70.0,
        "country_code": 15.0,
        "edit_distance": 15.0,
    },
    "id_code": {
        "exact_clean": 70.0,
        "prefix_match": 15.0,
        "levenshtein": 15.0,
    },
}


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Ensure weights sum to 100.0 by scaling proportionally if needed.
    """
    total = sum(weights.values())
    if total <= 0:
        count = len(weights)
        if count == 0:
            return {}
        return {k: 100.0 / count for k in weights}

    if abs(total - 100.0) < 0.001:
        return dict(weights)

    scale = 100.0 / total
    return {k: round(v * scale, 2) for k, v in weights.items()}


def get_weights_for_type(matching_type: str, custom_weights: Dict[str, float] = None) -> Dict[str, float]:
    """
    Get the weight profile for a specific matching type, applying any custom overrides.
    """
    profile_key = matching_type.lower()
    base = DEFAULT_WEIGHT_PROFILES.get(profile_key, DEFAULT_WEIGHT_PROFILES["generic_text"])

    if custom_weights:
        # Merge custom weights for keys that exist
        merged = dict(base)
        for k, v in custom_weights.items():
            if k in merged and isinstance(v, (int, float)):
                merged[k] = float(v)
        return normalize_weights(merged)

    return dict(base)
