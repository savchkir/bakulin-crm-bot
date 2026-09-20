from datetime import date
from crm_bot.date_utils import parse_date, is_due, format_date


def test_parse_date_handles_dd_mm():
    assert parse_date("20.09", reference_year=2026) == date(2026, 9, 20)


def test_parse_date_handles_dd_mm_yyyy():
    assert parse_date("20.09.2026") == date(2026, 9, 20)


def test_parse_date_returns_none_for_garbage():
    assert parse_date("на днях") is None


def test_is_due_true_for_today():
    assert is_due(date(2026, 9, 13), today=date(2026, 9, 13)) is True


def test_is_due_true_for_overdue():
    assert is_due(date(2026, 9, 10), today=date(2026, 9, 13)) is True


def test_is_due_false_for_future():
    assert is_due(date(2026, 9, 20), today=date(2026, 9, 13)) is False


def test_format_date():
    assert format_date(date(2026, 9, 20)) == "20.09"
