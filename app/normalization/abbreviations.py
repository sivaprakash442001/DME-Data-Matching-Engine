"""
Abbreviation dictionary and manager for text normalization.
Configurable, extensible, and domain-aware.
"""
import re
from typing import Dict, Optional


DEFAULT_COMPANY_ABBREVIATIONS: Dict[str, str] = {
    "pvt": "private",
    "pvt.": "private",
    "pvtltd": "private limited",
    "ltd": "limited",
    "ltd.": "limited",
    "llp": "limited liability partnership",
    "llp.": "limited liability partnership",
    "llc": "limited liability company",
    "llc.": "limited liability company",
    "co": "company",
    "co.": "company",
    "corp": "corporation",
    "corp.": "corporation",
    "inc": "incorporated",
    "inc.": "incorporated",
    "intl": "international",
    "intl.": "international",
    "plc": "public limited company",
    "plc.": "public limited company",
    "gmbh": "gmbh",
    "sa": "sociedad anonima",
    "ag": "aktiengesellschaft",
    "mfg": "manufacturing",
    "mfg.": "manufacturing",
    "tech": "technology",
    "tech.": "technology",
    "technologies": "technology",
    "serv": "services",
    "serv.": "services",
    "soln": "solutions",
    "solns": "solutions",
    "mgmt": "management",
    "mgmt.": "management",
    "assoc": "associates",
    "assoc.": "associates",
    "grp": "group",
    "grp.": "group",
    "ent": "enterprises",
    "ind": "industries",
    "inds": "industries",
    "sys": "systems",
    "comm": "communications",
}

DEFAULT_ADDRESS_ABBREVIATIONS: Dict[str, str] = {
    "rd": "road",
    "rd.": "road",
    "st": "street",
    "st.": "street",
    "ave": "avenue",
    "ave.": "avenue",
    "av": "avenue",
    "av.": "avenue",
    "blvd": "boulevard",
    "blvd.": "boulevard",
    "ln": "lane",
    "ln.": "lane",
    "dr": "drive",
    "dr.": "drive",
    "ct": "court",
    "ct.": "court",
    "pl": "place",
    "pl.": "place",
    "sq": "square",
    "sq.": "square",
    "cres": "crescent",
    "pkwy": "parkway",
    "hwy": "highway",
    "hwy.": "highway",
    "apt": "apartment",
    "apt.": "apartment",
    "ste": "suite",
    "ste.": "suite",
    "fl": "floor",
    "fl.": "floor",
    "bldg": "building",
    "bldg.": "building",
    "no": "number",
    "no.": "number",
    "nr": "near",
    "nr.": "near",
    "opp": "opposite",
    "opp.": "opposite",
    "adj": "adjacent",
    "ext": "extension",
    "ext.": "extension",
    "sect": "sector",
    "sec": "sector",
    "blk": "block",
    "hno": "house number",
    "h.no": "house number",
    "po box": "post office box",
    "p.o. box": "post office box",
    "p.o box": "post office box",
    "po": "post office",
    "p.o.": "post office",
    "dist": "district",
    "nagar": "nagar",
    "colony": "colony",
    "layout": "layout",
    "phase": "phase",
}

DEFAULT_DIRECTION_ABBREVIATIONS: Dict[str, str] = {
    "n": "north",
    "n.": "north",
    "s": "south",
    "s.": "south",
    "e": "east",
    "e.": "east",
    "w": "west",
    "w.": "west",
    "ne": "northeast",
    "ne.": "northeast",
    "nw": "northwest",
    "nw.": "northwest",
    "se": "southeast",
    "se.": "southeast",
    "sw": "southwest",
    "sw.": "southwest",
}

DEFAULT_NAME_ABBREVIATIONS: Dict[str, str] = {
    "dr": "doctor",
    "dr.": "doctor",
    "mr": "mister",
    "mr.": "mister",
    "mrs": "mistress",
    "mrs.": "mistress",
    "ms": "miss",
    "ms.": "miss",
    "prof": "professor",
    "prof.": "professor",
    "sr": "senior",
    "sr.": "senior",
    "jr": "junior",
    "jr.": "junior",
    "shri": "shri",
    "smt": "smt",
}

DEFAULT_STATE_MAPPINGS: Dict[str, str] = {
    # Indian States
    "tn": "tamil nadu",
    "t.n.": "tamil nadu",
    "ka": "karnataka",
    "mh": "maharashtra",
    "dl": "delhi",
    "kl": "kerala",
    "ap": "andhra pradesh",
    "ts": "telangana",
    "tg": "telangana",
    "wb": "west bengal",
    "up": "uttar pradesh",
    "mp": "madhya pradesh",
    "gj": "gujarat",
    "rj": "rajasthan",
    "hr": "haryana",
    "pb": "punjab",
    "or": "odisha",
    "br": "bihar",
    "jh": "jharkhand",
    "ct": "chhattisgarh",
    "ga": "goa",
    "as": "assam",
    # US States
    "ca": "california",
    "ny": "new york",
    "tx": "texas",
    "fl": "florida",
    "il": "illinois",
    "pa": "pennsylvania",
    "oh": "ohio",
    "ga": "georgia",
    "nc": "north carolina",
    "mi": "michigan",
    "nj": "new jersey",
    "va": "virginia",
    "wa": "washington",
    "az": "arizona",
    "ma": "massachusetts",
}


class AbbreviationManager:
    """
    Manages domain-specific abbreviation expansions with support for custom user overrides.
    """

    def __init__(self, custom_dict: Optional[Dict[str, str]] = None):
        self.categories: Dict[str, Dict[str, str]] = {
            "company": dict(DEFAULT_COMPANY_ABBREVIATIONS),
            "address": dict(DEFAULT_ADDRESS_ABBREVIATIONS),
            "direction": dict(DEFAULT_DIRECTION_ABBREVIATIONS),
            "name": dict(DEFAULT_NAME_ABBREVIATIONS),
            "state": dict(DEFAULT_STATE_MAPPINGS),
        }
        self.custom_dict: Dict[str, str] = {}
        if custom_dict:
            for k, v in custom_dict.items():
                self.custom_dict[k.strip().lower()] = v.strip().lower()
        self._compiled_regexes: Dict[str, re.Pattern] = {}

    def add_custom_rule(self, abbreviation: str, expansion: str):
        """Add or overwrite a custom abbreviation."""
        self.custom_dict[abbreviation.strip().lower()] = expansion.strip().lower()
        self._compiled_regexes.clear()

    def remove_custom_rule(self, abbreviation: str):
        """Remove a custom abbreviation."""
        key = abbreviation.strip().lower()
        if key in self.custom_dict:
            del self.custom_dict[key]
            self._compiled_regexes.clear()

    def clear_custom_rules(self):
        """Clear all custom abbreviations."""
        self.custom_dict.clear()
        self._compiled_regexes.clear()

    def get_all_abbreviations(self, category: Optional[str] = None) -> Dict[str, str]:
        """
        Return dictionary of abbreviations. If category is specified, return only that category,
        merged with custom rules.
        """
        combined: Dict[str, str] = {}
        if category == "address":
            combined.update(self.categories.get("address", {}))
            combined.update(self.categories.get("direction", {}))
            combined.update(self.categories.get("state", {}))
        elif category and category in self.categories:
            combined.update(self.categories[category])
        elif category is None or category == "all":
            for cat_dict in self.categories.values():
                combined.update(cat_dict)
        combined.update(self.custom_dict)
        return combined

    def expand_abbreviations(self, text: str, category: Optional[str] = None) -> str:
        """
        Expand abbreviations in text cleanly using word boundaries and punctuation awareness.
        """
        if not text:
            return ""

        abbrevs = self.get_all_abbreviations(category)
        if not abbrevs:
            return text

        # Sort abbreviations by length descending to match multi-word phrases first (e.g. 'pvt ltd' before 'pvt')
        sorted_keys = sorted(abbrevs.keys(), key=lambda x: len(x), reverse=True)

        result = f" {text} "
        delimiters = r"[\s,;/\-()\[\]{}:]"
        for abbr in sorted_keys:
            expansion = abbrevs[abbr]
            escaped_abbr = re.escape(abbr)
            pattern = rf"(?<={delimiters})({escaped_abbr})(?={delimiters})"
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)
            if not abbr.endswith("."):
                pattern_with_dot = rf"(?<={delimiters})({escaped_abbr}\.)(?={delimiters})"
                result = re.sub(pattern_with_dot, expansion, result, flags=re.IGNORECASE)

        return result.strip()


# Global default manager singleton
global_abbrev_manager = AbbreviationManager()
