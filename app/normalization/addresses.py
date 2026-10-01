"""
Address normalization and component parser module.
Extracts house number, street, locality, city, state, postal code, and country for entity resolution.
"""
import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict
from app.normalization.abbreviations import DEFAULT_STATE_MAPPINGS, global_abbrev_manager
from app.normalization.cleaner import default_normalizer, NormalizationSettings


@dataclass
class ParsedAddress:
    raw: str
    normalized: str
    house_number: Optional[str] = None
    street: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class AddressParser:
    """
    Parses unstructured address strings into address components.
    Works internationally, with robust heuristics for Indian, US, and generic international formats.
    """

    POSTAL_CODE_REGEX = re.compile(r"\b([0-9]{5,6}(?:-[0-9]{4})?)\b")
    # UK-style postcode regex: e.g. SW1A 1AA, EC1V 2NX
    UK_POSTAL_REGEX = re.compile(r"\b([A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2})\b", re.IGNORECASE)

    # Common Indian cities
    KNOWN_CITIES = {
        "chennai", "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", "kolkata",
        "pune", "ahmedabad", "jaipur", "surat", "lucknow", "kanpur", "nagpur", "indore",
        "thane", "bhopal", "visakhapatnam", "vadodara", "firozabad", "ludhiana", "rajkot",
        "agra", "siliguri", "nashik", "faridabad", "patiala", "meerut", "kalyan-dombivli",
        "vasai-virar", "varanasi", "srinagar", "dhanbad", "jodhpur", "amritsar", "raipur",
        "allahabad", "coimbatore", "jabalpur", "gwalior", "vijayawada", "madurai", "guwahati",
        "chandigarh", "hubli", "dharwad", "mysore", "mysuru", "tiruchirappalli", "bareilly",
        "aligarh", "tiruppur", "gurgaon", "gurugram", "noida", "navi mumbai", "kochi",
        # US/International cities
        "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia", "san antonio",
        "san diego", "dallas", "san jose", "austin", "jacksonville", "fort worth", "columbus",
        "charlotte", "san francisco", "indianapolis", "seattle", "denver", "washington", "boston",
        "london", "manchester", "birmingham", "toronto", "vancouver", "sydney", "melbourne",
        "singapore", "dubai"
    }

    def __init__(self):
        self.settings = NormalizationSettings(
            mode="standard",
            case_sensitive=False,
            remove_punctuation=True,
            normalize_whitespace=True,
            expand_abbreviations=True,
            normalize_numbers=True,
            category="address",
        )

    def parse(self, text: str) -> ParsedAddress:
        if not text:
            return ParsedAddress(raw="", normalized="")

        raw_str = str(text).strip()
        normalized = default_normalizer.normalize(raw_str, self.settings)

        postal_code = None
        # Try finding standard 5 or 6 digit postal code
        postal_match = self.POSTAL_CODE_REGEX.search(raw_str)
        if postal_match:
            postal_code = postal_match.group(1)
        else:
            uk_match = self.UK_POSTAL_REGEX.search(raw_str)
            if uk_match:
                postal_code = uk_match.group(1).upper()

        # Extract House/Plot/Building Number
        house_number = None
        house_match = re.search(r"\b(?:number\s+)?([0-9]{1,5}[a-z]?(?:[\/-][0-9]{1,5}[a-z]?)?)\b", normalized)
        if house_match:
            # Check it's not the postal code
            candidate = house_match.group(1)
            if candidate != postal_code:
                house_number = candidate

        # Extract State
        state = None
        # Check standard state mappings (e.g. TN -> tamil nadu, CA -> california)
        tokens = normalized.split()
        for token in tokens:
            if token in DEFAULT_STATE_MAPPINGS:
                state = DEFAULT_STATE_MAPPINGS[token]
                break

        if not state:
            # Check full state names
            for code, full_name in DEFAULT_STATE_MAPPINGS.items():
                if full_name in normalized:
                    state = full_name
                    break

        # Extract City
        city = None
        for known_city in sorted(self.KNOWN_CITIES, key=lambda x: len(x), reverse=True):
            if re.search(rf"\b{re.escape(known_city)}\b", normalized):
                city = known_city
                break

        # Extract Street / Road & Locality from comma separated segments or remaining tokens
        street = None
        locality = None

        # Look for road/street indicators in normalized text
        street_match = re.search(r"([a-z0-9\s]+?\b(?:road|street|avenue|boulevard|lane|drive|way|court|place|highway|circle)\b)", normalized)
        if street_match:
            street = street_match.group(1).strip()

        # Locality heuristic (e.g., "Anna Nagar", "T Nagar", "Sector 14", "Bandra West")
        locality_match = re.search(r"([a-z0-9\s]+?\b(?:nagar|colony|layout|sector|block|enclave|vihar|phase|estate|heights|hills|cross|main)\b(?:\s+(?:east|west|north|south))?)", normalized)
        if locality_match:
            locality = locality_match.group(1).strip()

        return ParsedAddress(
            raw=raw_str,
            normalized=normalized,
            house_number=house_number,
            street=street,
            locality=locality,
            city=city,
            state=state,
            postal_code=postal_code,
        )


default_address_parser = AddressParser()
