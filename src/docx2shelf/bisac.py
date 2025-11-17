from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Common BISAC subject headings for validation
BISAC_CATEGORIES = {
    # Fiction
    "FIC": {
        "name": "Fiction",
        "subcategories": {
            "FIC000000": "Fiction / General",
            "FIC002000": "Fiction / Action & Adventure",
            "FIC014000": "Fiction / Historical",
            "FIC019000": "Fiction / Literary",
            "FIC022000": "Fiction / Mystery & Detective",
            "FIC024000": "Fiction / Occult & Supernatural",
            "FIC028000": "Fiction / Romance",
            "FIC029000": "Fiction / Science Fiction",
            "FIC033000": "Fiction / Thrillers",
            "FIC045000": "Fiction / Family Life",
            "FIC051000": "Fiction / Contemporary Women",
            "FIC009000": "Fiction / Fantasy",
            "FIC030000": "Fiction / Short Stories",
            "FIC031000": "Fiction / Suspense",
            "FIC035000": "Fiction / War & Military",
        },
    },
    # Non-Fiction
    "BIO": {
        "name": "Biography & Autobiography",
        "subcategories": {
            "BIO000000": "Biography & Autobiography / General",
            "BIO026000": "Biography & Autobiography / Personal Memoirs",
            "BIO018000": "Biography & Autobiography / Literary",
            "BIO001000": "Biography & Autobiography / Artists, Architects, Photographers",
        },
    },
    "HIS": {
        "name": "History",
        "subcategories": {
            "HIS000000": "History / General",
            "HIS037070": "History / Modern",
            "HIS036000": "History / United States",
            "HIS010000": "History / Europe",
        },
    },
    "SEL": {
        "name": "Self-Help",
        "subcategories": {
            "SEL000000": "Self-Help / General",
            "SEL031000": "Self-Help / Personal Growth",
            "SEL027000": "Self-Help / Success",
            "SEL021000": "Self-Help / Motivational & Inspirational",
        },
    },
    "REL": {
        "name": "Religion",
        "subcategories": {
            "REL000000": "Religion / General",
            "REL006000": "Religion / Biblical Studies",
            "REL070000": "Religion / Christian Theology",
        },
    },
    "JUV": {
        "name": "Juvenile Fiction",
        "subcategories": {
            "JUV000000": "Juvenile Fiction / General",
            "JUV001000": "Juvenile Fiction / Action & Adventure",
            "JUV037000": "Juvenile Fiction / Fantasy & Magic",
            "JUV039000": "Juvenile Fiction / Social Themes",
        },
    },
    "YAF": {
        "name": "Young Adult Fiction",
        "subcategories": {
            "YAF000000": "Young Adult Fiction / General",
            "YAF001000": "Young Adult Fiction / Action & Adventure",
            "YAF019000": "Young Adult Fiction / Fantasy",
            "YAF058000": "Young Adult Fiction / Romance",
        },
    },
}

# Age range mappings
AGE_RANGES = {
    "0-2": "Baby/Toddler",
    "3-5": "Preschool",
    "6-8": "Early Elementary",
    "9-12": "Middle Grade",
    "13-17": "Young Adult",
    "18+": "Adult",
}

# Reading level mappings
READING_LEVELS = {
    "beginner": "Beginning Reader",
    "elementary": "Elementary",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "grade1": "Grade 1",
    "grade2": "Grade 2",
    "grade3": "Grade 3",
    "grade4": "Grade 4",
    "grade5": "Grade 5",
    "grade6": "Grade 6",
    "grade7": "Grade 7",
    "grade8": "Grade 8",
    "grade9": "Grade 9",
    "grade10": "Grade 10",
    "grade11": "Grade 11",
    "grade12": "Grade 12",
}


def validate_bisac_code(code: str) -> Tuple[bool, str]:
    """Validate a BISAC subject heading code.

    Returns (is_valid, error_message).
    """
    if not code:
        return False, "BISAC code cannot be empty"

    # Normalize code
    code = code.strip().upper()

    # Check format: 3 letters + 6 digits
    if not re.match(r"^[A-Z]{3}\d{6}$", code):
        return (
            False,
            f"BISAC code '{code}' must be 3 letters followed by 6 digits (e.g., FIC000000)",
        )

    # Check if category exists
    category = code[:3]
    if category not in BISAC_CATEGORIES:
        return False, f"Unknown BISAC category '{category}'"

    # Check if specific code exists
    if code not in BISAC_CATEGORIES[category]["subcategories"]:
        return False, f"BISAC code '{code}' not found in category '{category}'"

    return True, ""


def normalize_bisac_codes(codes: List[str]) -> Tuple[List[str], List[str]]:
    """Normalize and validate BISAC codes.

    Returns (valid_codes, errors).
    """
    valid_codes = []
    errors = []

    for code in codes:
        is_valid, error = validate_bisac_code(code)
        if is_valid:
            valid_codes.append(code.strip().upper())
        else:
            errors.append(error)

    return valid_codes, errors


def suggest_bisac_codes(keywords: List[str], genre_hints: Optional[List[str]] = None) -> List[str]:
    """Suggest BISAC codes based on keywords and genre hints."""
    suggestions = []

    # Keyword mappings to BISAC codes
    keyword_mappings = {
        "fantasy": ["FIC009000"],
        "science fiction": ["FIC029000"],
        "sci-fi": ["FIC029000"],
        "romance": ["FIC028000"],
        "mystery": ["FIC022000"],
        "thriller": ["FIC033000"],
        "historical": ["FIC014000"],
        "literary": ["FIC019000"],
        "adventure": ["FIC002000"],
        "contemporary": ["FIC051000"],
        "memoir": ["BIO026000"],
        "biography": ["BIO000000"],
        "self-help": ["SEL000000"],
        "motivational": ["SEL021000"],
        "young adult": ["YAF000000"],
        "children": ["JUV000000"],
        "juvenile": ["JUV000000"],
    }

    # Check keywords
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for key, codes in keyword_mappings.items():
            if key in keyword_lower:
                suggestions.extend(codes)

    # Check genre hints
    if genre_hints:
        for hint in genre_hints:
            hint_lower = hint.lower()
            for key, codes in keyword_mappings.items():
                if key in hint_lower:
                    suggestions.extend(codes)

    # Remove duplicates and return
    return list(set(suggestions))


def get_bisac_description(code: str) -> Optional[str]:
    """Get human-readable description for a BISAC code."""
    if not code:
        return None

    code = code.strip().upper()
    category = code[:3]

    if category in BISAC_CATEGORIES:
        return BISAC_CATEGORIES[category]["subcategories"].get(code)

    return None


def validate_age_range(age_range: str) -> Tuple[bool, str]:
    """Validate age range format."""
    if not age_range:
        return True, ""  # Optional field

    # Common patterns
    patterns = [
        r"^\d+-\d+$",  # e.g., "8-12"
        r"^\d+\+$",  # e.g., "18+"
        r"^\d+$",  # e.g., "5"
    ]

    for pattern in patterns:
        if re.match(pattern, age_range):
            return True, ""

    # Check predefined ranges
    if age_range in AGE_RANGES:
        return True, ""

    return (
        False,
        f"Invalid age range format: '{age_range}'. Use formats like '8-12', '18+', or predefined ranges.",
    )


def validate_reading_level(level: str) -> Tuple[bool, str]:
    """Validate reading level."""
    if not level:
        return True, ""  # Optional field

    level_lower = level.lower()

    if level_lower in READING_LEVELS:
        return True, ""

    # Check for grade level patterns
    if re.match(r"^grade\s*\d{1,2}$", level_lower):
        return True, ""

    return False, f"Invalid reading level: '{level}'. Use predefined levels or 'Grade X' format."


def normalize_keywords(keywords: List[str]) -> List[str]:
    """Normalize and clean keywords."""
    normalized = []

    for keyword in keywords:
        # Clean whitespace and convert to title case
        clean_keyword = keyword.strip().title()

        # Remove duplicates
        if clean_keyword and clean_keyword not in normalized:
            normalized.append(clean_keyword)

    return normalized


def validate_isbn_format(isbn: str, isbn_type: str = "ISBN-13") -> Tuple[bool, str]:
    """Validate ISBN format and checksum."""
    if not isbn:
        return True, ""  # Optional field

    # Remove hyphens and spaces
    clean_isbn = re.sub(r"[-\s]", "", isbn)

    if isbn_type == "ISBN-13":
        if len(clean_isbn) != 13:
            return False, f"ISBN-13 must be 13 digits, got {len(clean_isbn)}"

        if not clean_isbn.isdigit():
            return False, "ISBN-13 must contain only digits"

        # Validate checksum
        checksum = 0
        for i, digit in enumerate(clean_isbn[:12]):
            weight = 1 if i % 2 == 0 else 3
            checksum += int(digit) * weight

        check_digit = (10 - (checksum % 10)) % 10
        if check_digit != int(clean_isbn[12]):
            return False, "Invalid ISBN-13 checksum"

    elif isbn_type == "ISBN-10":
        if len(clean_isbn) != 10:
            return False, f"ISBN-10 must be 10 characters, got {len(clean_isbn)}"

        # ISBN-10 can have X as last character
        if not clean_isbn[:-1].isdigit() or (clean_isbn[-1] not in "0123456789X"):
            return False, "Invalid ISBN-10 format"

    return True, ""


def generate_metadata_report(metadata) -> str:
    """Generate a comprehensive metadata validation report."""
    lines = ["Metadata Validation Report", "=" * 30]

    # Basic validation
    required_fields = ["title", "author", "language"]
    missing_required = []

    for field in required_fields:
        if not getattr(metadata, field, None):
            missing_required.append(field)

    if missing_required:
        lines.append(f"❌ Missing required fields: {', '.join(missing_required)}")
    else:
        lines.append("✅ All required fields present")

    # BISAC validation
    if hasattr(metadata, "bisac_codes") and metadata.bisac_codes:
        valid_codes, errors = normalize_bisac_codes(metadata.bisac_codes)
        lines.append(f"📚 BISAC Codes: {len(valid_codes)} valid, {len(errors)} errors")

        for error in errors[:3]:  # Show first 3 errors
            lines.append(f"   ⚠️ {error}")

        if len(errors) > 3:
            lines.append(f"   ... and {len(errors) - 3} more errors")

    # ISBN validation
    if hasattr(metadata, "isbn") and metadata.isbn:
        is_valid, error = validate_isbn_format(metadata.isbn)
        if is_valid:
            lines.append("✅ ISBN format valid")
        else:
            lines.append(f"❌ ISBN error: {error}")

    # Age range validation
    if hasattr(metadata, "age_range") and metadata.age_range:
        is_valid, error = validate_age_range(metadata.age_range)
        if is_valid:
            lines.append("✅ Age range valid")
        else:
            lines.append(f"❌ Age range error: {error}")

    return "\n".join(lines)
