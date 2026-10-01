"""
Core text cleaning and normalization engine.
Supports Conservative, Standard, and Aggressive normalization modes with granular user controls.
"""
import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import List, Optional
from app.normalization.abbreviations import AbbreviationManager, global_abbrev_manager
from app.normalization.numbers import normalize_number_expressions


# Standard punctuation to strip in standard mode
PUNCTUATION_CHARS = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""

# Common stopwords that can optionally be filtered
DEFAULT_STOPWORDS = {
    "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "a", "an", "by"
}


@dataclass
class NormalizationSettings:
    """Configurable normalization options."""
    mode: str = "standard"  # 'conservative', 'standard', 'aggressive'
    case_sensitive: bool = False
    remove_punctuation: bool = True
    normalize_whitespace: bool = True
    expand_abbreviations: bool = True
    normalize_numbers: bool = True
    remove_accents: bool = True
    remove_stopwords: bool = False
    category: Optional[str] = None  # 'company', 'address', 'name', etc.

    def to_dict(self):
        return asdict(self)


class TextNormalizer:
    """
    Normalizes arbitrary text based on specified mode and settings.
    """

    def __init__(self, abbrev_manager: Optional[AbbreviationManager] = None):
        self.abbrev_manager = abbrev_manager or global_abbrev_manager

    def remove_accents(self, text: str) -> str:
        """Strip diacritics / accents (e.g., café -> cafe, München -> Munchen)."""
        nfkd_form = unicodedata.normalize("NFKD", text)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def normalize(self, text: str, settings: Optional[NormalizationSettings] = None) -> str:
        """
        Normalize input text using provided settings or sensible defaults.
        """
        if text is None:
            return ""

        text = str(text)
        if not text.strip():
            return ""

        settings = settings or NormalizationSettings()
        mode = settings.mode.lower()

        # Step 1: Accents
        if settings.remove_accents:
            text = self.remove_accents(text)

        # Step 2: Case
        if not settings.case_sensitive:
            text = text.lower()

        # Step 3: Conservative vs Standard vs Aggressive logic
        if mode == "conservative":
            # In conservative mode, preserve meaningful punctuation (like @, +, hyphens in codes)
            # Only collapse spaces and strip outer whitespace
            if settings.normalize_whitespace:
                text = re.sub(r"\s+", " ", text).strip()
            return text

        # Step 4: Number normalization
        if settings.normalize_numbers:
            text = normalize_number_expressions(text)

        # Step 5: Abbreviation expansion (before stripping punctuation so "pvt." or "st." matches)
        if settings.expand_abbreviations:
            text = self.abbrev_manager.expand_abbreviations(text, category=settings.category)

        # Step 6: Punctuation removal
        if settings.remove_punctuation or mode == "aggressive":
            if mode == "aggressive":
                # Remove all non-alphanumeric except space
                text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
            else:
                # Replace common punctuation with space to prevent words from sticking together
                # e.g., "12-A, MG Road / Chennai" -> "12 A  MG Road   Chennai"
                text = re.sub(r"[\.,\-_\/\\()[\]{}:;'\"#&~+=?!$*@%|><]", " ", text)

        # Step 7: Collapse whitespace
        if settings.normalize_whitespace:
            text = re.sub(r"\s+", " ", text).strip()

        # Step 8: Optional stopword removal
        if settings.remove_stopwords:
            tokens = text.split()
            tokens = [t for t in tokens if t not in DEFAULT_STOPWORDS]
            text = " ".join(tokens)

        return text

    def tokenize(self, text: str, settings: Optional[NormalizationSettings] = None) -> List[str]:
        """
        Normalize text and return list of tokens.
        """
        normalized = self.normalize(text, settings)
        if not normalized:
            return []
        return [t for t in normalized.split() if t]


# Default normalizer instance
default_normalizer = TextNormalizer()
