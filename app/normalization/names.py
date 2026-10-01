"""
Person name normalization and parser module.
Handles honorifics, suffixes, inverted orders ("Smith, John"), middle names, and initials.
"""
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from app.normalization.cleaner import default_normalizer, NormalizationSettings


TITLES = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "sir", "madam", "shri", "smt", "shree", "rev", "pastor"
}

SUFFIXES = {
    "jr", "sr", "ii", "iii", "iv", "v", "phd", "md", "esq", "cpa"
}


@dataclass
class ParsedName:
    raw: str
    normalized: str
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_names: List[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    initials: List[str] = None

    def __post_init__(self):
        if self.middle_names is None:
            self.middle_names = []
        if self.initials is None:
            self.initials = []

    def to_dict(self) -> Dict:
        return asdict(self)


class PersonNameParser:
    """
    Parses unstructured person names into structured components.
    """

    def __init__(self):
        self.settings = NormalizationSettings(
            mode="standard",
            case_sensitive=False,
            remove_punctuation=True,
            normalize_whitespace=True,
            expand_abbreviations=False,
            normalize_numbers=False,
            category="name",
        )

    def parse(self, text: str) -> ParsedName:
        if not text:
            return ParsedName(raw="", normalized="")

        raw_str = str(text).strip()
        has_comma = "," in raw_str

        # If comma present e.g. "Smith, John M."
        # parts before comma is likely last name, after is first/middle
        parts_by_comma = [p.strip() for p in raw_str.split(",") if p.strip()]

        normalized = default_normalizer.normalize(raw_str, self.settings)
        tokens = normalized.split()

        if not tokens:
            return ParsedName(raw=raw_str, normalized=normalized)

        # Detect Title
        title = None
        if tokens and tokens[0] in TITLES:
            title = tokens.pop(0)

        # Detect Suffix
        suffix = None
        if tokens and tokens[-1] in SUFFIXES:
            suffix = tokens.pop(-1)

        if not tokens:
            return ParsedName(raw=raw_str, normalized=normalized, title=title, suffix=suffix)

        first_name = None
        middle_names = []
        last_name = None

        if has_comma and len(parts_by_comma) >= 2:
            # "Smith, John Michael"
            last_tokens = default_normalizer.normalize(parts_by_comma[0], self.settings).split()
            first_middle_tokens = default_normalizer.normalize(" ".join(parts_by_comma[1:]), self.settings).split()

            # Clean titles/suffixes from token lists
            last_tokens = [t for t in last_tokens if t not in TITLES and t not in SUFFIXES]
            first_middle_tokens = [t for t in first_middle_tokens if t not in TITLES and t not in SUFFIXES]

            if last_tokens:
                last_name = " ".join(last_tokens)
            if first_middle_tokens:
                first_name = first_middle_tokens[0]
                middle_names = first_middle_tokens[1:]
        else:
            if len(tokens) == 1:
                first_name = tokens[0]
            elif len(tokens) == 2:
                first_name = tokens[0]
                last_name = tokens[1]
            else:
                first_name = tokens[0]
                middle_names = tokens[1:-1]
                last_name = tokens[-1]

        # Extract initials
        all_name_tokens = ([first_name] if first_name else []) + middle_names + ([last_name] if last_name else [])
        initials = [t[0] for t in all_name_tokens if t]

        return ParsedName(
            raw=raw_str,
            normalized=normalized,
            title=title,
            first_name=first_name,
            middle_names=middle_names,
            last_name=last_name,
            suffix=suffix,
            initials=initials,
        )


default_name_parser = PersonNameParser()
