"""
Comprehensive test suite for Data Matching Engine.
Validates normalization, algorithms, specialized matchers, auto-detection, and edge cases.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.normalization.cleaner import default_normalizer, NormalizationSettings
from app.normalization.abbreviations import global_abbrev_manager
from app.matching.engine import default_engine
from app.matching.detector import detect_single_value_type, detect_column_type
from app.matching.algorithms import (
    levenshtein_similarity,
    jaro_winkler_similarity,
    token_sort_ratio,
    token_set_ratio,
)


def test_normalization_examples():
    # ABC Pvt. Ltd. -> abc private limited
    norm_1 = default_normalizer.normalize("ABC Pvt. Ltd.")
    assert "private limited" in norm_1
    assert "abc" in norm_1

    # 12-A, MG Road / Chennai -> 12 a mg road chennai
    norm_2 = default_normalizer.normalize("12-A, MG Road / Chennai")
    assert "road" in norm_2
    assert "chennai" in norm_2


def test_abbreviation_custom_rules():
    global_abbrev_manager.add_custom_rule("beng", "bengaluru")
    res = global_abbrev_manager.expand_abbreviations("beng central")
    assert "bengaluru central" == res
    global_abbrev_manager.remove_custom_rule("beng")


def test_address_matcher_examples():
    # 12, MG Road, Chennai vs 12 MG Rd Chennai -> Strong Match
    res1 = default_engine.match_pair("12, MG Road, Chennai", "12 MG Rd Chennai", matching_type="address")
    assert res1.score >= 90.0, f"Expected >= 90, got {res1.score}"
    assert res1.status == "Strong Match"

    # 45 Anna Nagar West vs 45 Anna Nagar W -> Strong Match
    res2 = default_engine.match_pair("45 Anna Nagar West", "45 Anna Nagar W", matching_type="address")
    assert res2.score >= 88.0, f"Expected >= 88, got {res2.score}"
    assert res2.status in ("Strong Match", "Likely Match")

    # 100 Main Street vs 200 Main Street -> House number discrepancy -> Possible Match
    res3 = default_engine.match_pair("100 Main Street", "200 Main Street", matching_type="address")
    assert 30.0 <= res3.score <= 65.0, f"Expected between 30 and 65, got {res3.score}"
    assert res3.status == "Possible Match"

    # Chennai, Tamil Nadu vs Mumbai, Maharashtra -> No Match
    res4 = default_engine.match_pair("Chennai, Tamil Nadu", "Mumbai, Maharashtra", matching_type="address")
    assert res4.score <= 25.0, f"Expected <= 25, got {res4.score}"
    # 12-A, MG Road, Chennai vs 12 MG Road Chennai -> Alphanumeric house number handling
    res5 = default_engine.match_pair("12-A, MG Road, Chennai", "12 MG Road Chennai", matching_type="address")
    assert res5.score >= 80.0, f"Expected >= 80, got {res5.score}"


def test_company_matcher_examples():
    # ABC Pvt. Ltd. vs abc private limited
    res1 = default_engine.match_pair("ABC Pvt. Ltd.", "abc private limited", matching_type="company")
    assert res1.score >= 95.0, f"Expected >= 95, got {res1.score}"
    assert res1.status == "Strong Match"

    # ABC PVT LTD vs ABC Private Limited
    res2 = default_engine.match_pair("ABC PVT LTD", "ABC Private Limited", matching_type="company")
    assert res2.score >= 95.0, f"Expected >= 95, got {res2.score}"
    assert res2.status == "Strong Match"

    # A.B.C. PVT. LTD. vs ABC PRIVATE LTD
    res3 = default_engine.match_pair("A.B.C. PVT. LTD.", "ABC PRIVATE LTD", matching_type="company")
    assert res3.score >= 95.0, f"Expected >= 95, got {res3.score}"


def test_person_name_matcher_examples():
    # John Michael Smith vs Smith, John M.
    res1 = default_engine.match_pair("John Michael Smith", "Smith, John M.", matching_type="person_name")
    assert res1.score >= 90.0, f"Expected >= 90, got {res1.score}"
    assert res1.status == "Strong Match"

    # John Smith vs Smith John
    res2 = default_engine.match_pair("John Smith", "Smith John", matching_type="person_name")
    assert res2.score >= 95.0, f"Expected >= 95, got {res2.score}"

    # John A Smith vs John Albert Smith
    res3 = default_engine.match_pair("John A Smith", "John Albert Smith", matching_type="person_name")
    assert res3.score >= 88.0, f"Expected >= 88, got {res3.score}"


def test_email_matcher_examples():
    # John.Smith@gmail.com vs john.smith@gmail.com -> 100%
    res1 = default_engine.match_pair("John.Smith@gmail.com", "john.smith@gmail.com", matching_type="email")
    assert res1.score == 100.0

    # johnsmith@gmail.com vs john.smith@gmail.com -> conservative score (not 100%)
    res2 = default_engine.match_pair("johnsmith@gmail.com", "john.smith@gmail.com", matching_type="email")
    assert 80.0 <= res2.score <= 95.0, f"Expected between 80 and 95, got {res2.score}"

    # Different domains -> very low score
    res3 = default_engine.match_pair("john@gmail.com", "john@yahoo.com", matching_type="email")
    assert res3.score <= 30.0


def test_phone_matcher_examples():
    # +91 98765 43210 vs 09876543210 vs 9876543210
    res1 = default_engine.match_pair("+91 98765 43210", "9876543210", matching_type="phone")
    assert res1.score >= 95.0, f"Expected >= 95, got {res1.score}"

    res2 = default_engine.match_pair("09876543210", "9876543210", matching_type="phone")
    assert res2.score >= 95.0, f"Expected >= 95, got {res2.score}"


def test_type_detection():
    assert detect_single_value_type("john.smith@gmail.com") == "email"
    assert detect_single_value_type("+91 9876543210") == "phone"
    assert detect_single_value_type("ABC Pvt. Ltd.") == "company"
    assert detect_single_value_type("12, MG Road, Chennai") == "address"


if __name__ == "__main__":
    test_normalization_examples()
    test_abbreviation_custom_rules()
    test_address_matcher_examples()
    test_company_matcher_examples()
    test_person_name_matcher_examples()
    test_email_matcher_examples()
    test_phone_matcher_examples()
    test_type_detection()
    print("All unit tests passed successfully!")
