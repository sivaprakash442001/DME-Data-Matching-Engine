"""
Modular similarity algorithms for entity matching.
Includes Levenshtein, Damerau-Levenshtein, Jaro, Jaro-Winkler, Token Sort,
Token Set, Jaccard, Partial substring matching, N-Gram similarity, and Exact match.
All metrics return scores on a 0.0 - 100.0 scale.
"""
from typing import List, Set, Union, Optional
import math

try:
    from rapidfuzz import fuzz, distance
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


def exact_match_score(s1: str, s2: str) -> float:
    """Returns 100.0 if s1 == s2, else 0.0."""
    if s1 is None or s2 is None:
        return 0.0
    return 100.0 if s1 == s2 else 0.0


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Normalized Levenshtein similarity score (0.0 to 100.0).
    Ratio = (max_len - distance) / max_len * 100.
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(distance.Levenshtein.normalized_similarity(s1, s2) * 100.0)

    # Pure Python fallback
    len1, len2 = len(s1), len(s2)
    max_len = max(len1, len2)
    if max_len == 0:
        return 100.0

    dp = list(range(len2 + 1))
    for i, c1 in enumerate(s1):
        new_dp = [i + 1] * (len2 + 1)
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            new_dp[j + 1] = min(
                dp[j + 1] + 1,      # deletion
                new_dp[j] + 1,      # insertion
                dp[j] + cost        # substitution
            )
        dp = new_dp
    dist = dp[len2]
    return max(0.0, min(100.0, (1.0 - (dist / max_len)) * 100.0))


def damerau_levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Damerau-Levenshtein similarity (0.0 to 100.0), which accounts for insertions,
    deletions, substitutions, and transpositions of two adjacent characters.
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(distance.DamerauLevenshtein.normalized_similarity(s1, s2) * 100.0)

    # Pure Python implementation
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 100.0

    d = {}
    len1, len2 = len(s1), len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,       # deletion
                d[(i, j - 1)] + 1,       # insertion
                d[(i - 1, j - 1)] + cost # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost) # transposition

    dist = d[(len1 - 1, len2 - 1)]
    return max(0.0, min(100.0, (1.0 - (dist / max_len)) * 100.0))


def jaro_similarity(s1: str, s2: str) -> float:
    """
    Jaro similarity metric (0.0 to 100.0).
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(distance.Jaro.similarity(s1, s2) * 100.0)

    # Pure Python fallback
    len1, len2 = len(s1), len(s2)
    match_distance = (max(len1, len2) // 2) - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = ((matches / len1) + (matches / len2) + ((matches - transpositions / 2.0) / matches)) / 3.0
    return float(jaro * 100.0)


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """
    Jaro-Winkler similarity (0.0 to 100.0), gives higher weight to prefix matches.
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(distance.JaroWinkler.similarity(s1, s2, prefix_weight=prefix_weight) * 100.0)

    jaro = jaro_similarity(s1, s2) / 100.0
    prefix_len = 0
    max_prefix = min(4, len(s1), len(s2))
    for i in range(max_prefix):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    jw = jaro + (prefix_len * prefix_weight * (1.0 - jaro))
    return float(min(1.0, max(0.0, jw)) * 100.0)


def token_sort_ratio(s1: str, s2: str) -> float:
    """
    Token Sort Ratio (0.0 to 100.0).
    Sorts tokens alphabetically and then computes string similarity.
    Useful for reordered tokens like: "John Smith" vs "Smith John"
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(fuzz.token_sort_ratio(s1, s2))

    t1 = " ".join(sorted(s1.split()))
    t2 = " ".join(sorted(s2.split()))
    return levenshtein_similarity(t1, t2)


def token_set_ratio(s1: str, s2: str) -> float:
    """
    Token Set Ratio (0.0 to 100.0).
    Finds intersection of tokens and compares intersection with remaining tokens.
    Handles duplicate tokens and substring containment gracefully.
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(fuzz.token_set_ratio(s1, s2))

    tokens1 = set(s1.split())
    tokens2 = set(s2.split())

    intersection = tokens1.intersection(tokens2)
    diff1to2 = tokens1.difference(tokens2)
    diff2to1 = tokens2.difference(tokens1)

    sorted_intersect = " ".join(sorted(intersection))
    sorted_diff1to2 = " ".join(sorted(diff1to2))
    sorted_diff2to1 = " ".join(sorted(diff2to1))

    combined_1to2 = (sorted_intersect + " " + sorted_diff1to2).strip()
    combined_2to1 = (sorted_intersect + " " + sorted_diff2to1).strip()

    scores = [
        levenshtein_similarity(sorted_intersect, combined_1to2) if sorted_intersect else 0.0,
        levenshtein_similarity(sorted_intersect, combined_2to1) if sorted_intersect else 0.0,
        levenshtein_similarity(combined_1to2, combined_2to1),
    ]
    return max(scores)


def jaccard_similarity(tokens1: Union[str, List[str], Set[str]], tokens2: Union[str, List[str], Set[str]]) -> float:
    """
    Jaccard token similarity (0.0 to 100.0).
    Ratio of intersection of words over union of words.
    """
    if isinstance(tokens1, str):
        set1 = set(tokens1.split())
    else:
        set1 = set(tokens1)

    if isinstance(tokens2, str):
        set2 = set(tokens2.split())
    else:
        set2 = set(tokens2)

    if not set1 and not set2:
        return 100.0
    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0.0

    return float(len(intersection) / len(union) * 100.0)


def partial_ratio(s1: str, s2: str) -> float:
    """
    Partial Ratio (0.0 to 100.0).
    Finds the score of the best matching substring of the longer string with the shorter string.
    Useful when one string contains another: "ABC PRIVATE LIMITED" vs "ABC PRIVATE LIMITED CHENNAI"
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    if HAS_RAPIDFUZZ:
        return float(fuzz.partial_ratio(s1, s2))

    shorter, longer = (s1, s2) if len(s1) <= len(s2) else (s2, s1)
    if shorter in longer:
        return 100.0

    len_short = len(shorter)
    max_score = 0.0
    for i in range(len(longer) - len_short + 1):
        sub = longer[i:i + len_short]
        score = levenshtein_similarity(shorter, sub)
        if score > max_score:
            max_score = score
            if max_score >= 100.0:
                break
    return max_score


def ngram_similarity(s1: str, s2: str, n: int = 3) -> float:
    """
    N-gram Dice similarity (0.0 to 100.0).
    Breaks strings into character n-grams and calculates overlap coefficient.
    """
    if s1 is None or s2 is None:
        return 0.0
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    def get_ngrams(s: str, n_val: int) -> Set[str]:
        padded = f"^{s}$"
        if len(padded) < n_val:
            return {padded}
        return {padded[i:i+n_val] for i in range(len(padded) - n_val + 1)}

    ngrams1 = get_ngrams(s1, n)
    ngrams2 = get_ngrams(s2, n)

    if not ngrams1 and not ngrams2:
        return 100.0
    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1.intersection(ngrams2))
    total = len(ngrams1) + len(ngrams2)
    dice = (2.0 * intersection) / total
    return float(dice * 100.0)


def compute_all_metrics(s1: str, s2: str) -> dict[str, float]:
    """
    Compute a full dictionary of standard similarity scores.
    """
    return {
        "exact_match": exact_match_score(s1, s2),
        "levenshtein": round(levenshtein_similarity(s1, s2), 1),
        "damerau_levenshtein": round(damerau_levenshtein_similarity(s1, s2), 1),
        "jaro": round(jaro_similarity(s1, s2), 1),
        "jaro_winkler": round(jaro_winkler_similarity(s1, s2), 1),
        "token_sort": round(token_sort_ratio(s1, s2), 1),
        "token_set": round(token_set_ratio(s1, s2), 1),
        "jaccard": round(jaccard_similarity(s1, s2), 1),
        "partial_match": round(partial_ratio(s1, s2), 1),
        "ngram": round(ngram_similarity(s1, s2, n=3), 1),
    }
