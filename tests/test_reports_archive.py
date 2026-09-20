# bakulin-crm-bot/tests/test_reports_archive.py
from crm_bot.reports_archive import append_report, list_reports, find_report_for_period


class FakeRowsGateway:
    """In-memory stand-in for a row-oriented worksheet (header row + data rows)."""

    def __init__(self, rows=None):
        self.rows = rows or [["period_start", "period_end", "generated_at", "text"]]

    def get_all_rows(self) -> list:
        return self.rows[1:]  # skip header

    def append_row(self, row: list) -> None:
        self.rows.append(row)


def test_append_report_adds_a_row():
    gateway = FakeRowsGateway()
    append_report(gateway, period_start="2026-09-07", period_end="2026-09-13",
                   generated_at="2026-09-11T19:00:00", text="Всё по плану")
    assert gateway.get_all_rows() == [
        ["2026-09-07", "2026-09-13", "2026-09-11T19:00:00", "Всё по плану"]
    ]


def test_list_reports_returns_structured_dicts():
    gateway = FakeRowsGateway(rows=[
        ["period_start", "period_end", "generated_at", "text"],
        ["2026-09-07", "2026-09-13", "2026-09-11T19:00:00", "Отчёт за неделю 1"],
    ])
    reports = list_reports(gateway)
    assert reports == [
        {
            "period_start": "2026-09-07",
            "period_end": "2026-09-13",
            "generated_at": "2026-09-11T19:00:00",
            "text": "Отчёт за неделю 1",
        }
    ]


def test_find_report_for_period_returns_exact_match():
    gateway = FakeRowsGateway(rows=[
        ["period_start", "period_end", "generated_at", "text"],
        ["2026-08-31", "2026-09-06", "2026-09-04T19:00:00", "Старый отчёт"],
        ["2026-09-07", "2026-09-13", "2026-09-11T19:00:00", "Отчёт за неделю 1"],
    ])
    reports = list_reports(gateway)
    found = find_report_for_period(reports, period_start="2026-09-07", period_end="2026-09-13")
    assert found["text"] == "Отчёт за неделю 1"


def test_find_report_for_period_returns_none_when_absent():
    gateway = FakeRowsGateway()
    reports = list_reports(gateway)
    assert find_report_for_period(reports, period_start="2026-01-01", period_end="2026-01-07") is None
