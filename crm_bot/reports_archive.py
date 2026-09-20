# bakulin-crm-bot/crm_bot/reports_archive.py
from typing import Optional


def append_report(gateway, period_start: str, period_end: str, generated_at: str, text: str) -> None:
    gateway.append_row([period_start, period_end, generated_at, text])


def list_reports(gateway) -> list:
    return [
        {
            "period_start": row[0],
            "period_end": row[1],
            "generated_at": row[2],
            "text": row[3],
        }
        for row in gateway.get_all_rows()
        if len(row) >= 4
    ]


def find_report_for_period(reports: list, period_start: str, period_end: str) -> Optional[dict]:
    for report in reports:
        if report["period_start"] == period_start and report["period_end"] == period_end:
            return report
    return None
