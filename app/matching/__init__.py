"""
Matching package export.
"""
from app.matching.algorithms import (
    exact_match_score,
    levenshtein_similarity,
    damerau_levenshtein_similarity,
    jaro_similarity,
    jaro_winkler_similarity,
    token_sort_ratio,
    token_set_ratio,
    jaccard_similarity,
    partial_ratio,
    ngram_similarity,
    compute_all_metrics,
)
from app.matching.detector import detect_column_type, detect_single_value_type
from app.matching.generic import GenericTextMatcher, default_generic_matcher
from app.matching.address import AddressMatcher, default_address_matcher
from app.matching.name import PersonNameMatcher, default_name_matcher
from app.matching.company import CompanyNameMatcher, default_company_matcher
from app.matching.email import EmailMatcher, default_email_matcher
from app.matching.phone import PhoneMatcher, default_phone_matcher
from app.matching.id_code import IdCodeMatcher, default_id_code_matcher
from app.matching.engine import MatchingEngine, default_engine

__all__ = [
    "exact_match_score",
    "levenshtein_similarity",
    "damerau_levenshtein_similarity",
    "jaro_similarity",
    "jaro_winkler_similarity",
    "token_sort_ratio",
    "token_set_ratio",
    "jaccard_similarity",
    "partial_ratio",
    "ngram_similarity",
    "compute_all_metrics",
    "detect_column_type",
    "detect_single_value_type",
    "GenericTextMatcher",
    "default_generic_matcher",
    "AddressMatcher",
    "default_address_matcher",
    "PersonNameMatcher",
    "default_name_matcher",
    "CompanyNameMatcher",
    "default_company_matcher",
    "EmailMatcher",
    "default_email_matcher",
    "PhoneMatcher",
    "default_phone_matcher",
    "IdCodeMatcher",
    "default_id_code_matcher",
    "MatchingEngine",
    "default_engine",
]
