"""
Date normalisation utilities.
Handles SAP (YYYYMMDD), European (DD.MM.YYYY), ISO, and US formats.
"""
from datetime import date, datetime


# Ordered by specificity — try the most restrictive first.
DATE_FORMATS = [
    '%Y%m%d',        # SAP: 20240115
    '%d.%m.%Y',      # German/European: 15.01.2024
    '%Y-%m-%d',      # ISO: 2024-01-15
    '%m/%d/%Y',      # US: 01/15/2024
    '%d/%m/%Y',      # UK: 15/01/2024
    '%Y/%m/%d',      # Alternate ISO: 2024/01/15
]


def parse_date(value: str) -> date:
    """
    Attempt to parse a date string using common formats.
    Raises ValueError if none match.
    """
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) else value.date()

    cleaned = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: '{value}'. Tried formats: {DATE_FORMATS}")


def safe_parse_date(value: str, fallback: date | None = None) -> date | None:
    """Parse a date, returning fallback on failure instead of raising."""
    try:
        return parse_date(value)
    except (ValueError, TypeError):
        return fallback
