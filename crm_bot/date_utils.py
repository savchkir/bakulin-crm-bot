from datetime import date, datetime
from typing import Optional


def parse_date(text: str, reference_year: Optional[int] = None) -> Optional[date]:
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        parsed = datetime.strptime(text, "%d.%m")
        year = reference_year or date.today().year
        return date(year, parsed.month, parsed.day)
    except ValueError:
        return None


def is_due(target_date: date, today: date) -> bool:
    return target_date <= today


def format_date(value: date) -> str:
    return value.strftime("%d.%m")
