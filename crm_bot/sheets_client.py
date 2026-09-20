# bakulin-crm-bot/crm_bot/sheets_client.py
import argparse
import json
import sys

from crm_bot.config import load_config
from crm_bot.lead_matcher import match_lead
from crm_bot.reports_archive import append_report, list_reports, find_report_for_period
from crm_bot.sheets_schema import (
    FIELD_ROW_LABELS,
    NEW_BLOCK_LABELS,
    find_row_by_label,
    validate_status,
    RowLabelNotFound,
)

FIRST_LEAD_COLUMN = 2  # column A = labels, column B onward = real leads (no template/example column)


class GspreadGateway:
    """Thin real adapter over gspread.Worksheet. Not covered by unit tests directly —
    exercised only in the manual smoke test in README.md."""

    def __init__(self, worksheet):
        self.worksheet = worksheet

    def get_column(self, col: int) -> list:
        return self.worksheet.col_values(col)

    def last_used_column(self) -> int:
        # Row 1 is only a sheet title (content in column A only) — real lead data
        # starts several rows down (row 4+), so we must scan every row's width,
        # not just row 1, to find the true last used column.
        all_values = self.worksheet.get_all_values()
        return max((len(row) for row in all_values), default=1)

    def update_cell(self, row: int, col: int, value: str) -> None:
        self.worksheet.update_cell(row, col, value)


def open_gateway(config) -> GspreadGateway:
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        config.google_service_account_json, scopes=scopes
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.sheet_id)
    worksheet = spreadsheet.worksheet(config.sheet_worksheet_name)
    return GspreadGateway(worksheet)


class ReportsRowsGateway:
    """Thin real adapter over a row-oriented gspread.Worksheet (the 'Звіти' tab)."""

    def __init__(self, worksheet):
        self.worksheet = worksheet

    def get_all_rows(self) -> list:
        return self.worksheet.get_all_values()[1:]  # skip header row

    def append_row(self, row: list) -> None:
        self.worksheet.append_row(row)


def open_reports_gateway(config) -> ReportsRowsGateway:
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread.exceptions import WorksheetNotFound

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        config.google_service_account_json, scopes=scopes
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.sheet_id)
    try:
        worksheet = spreadsheet.worksheet(config.reports_worksheet_name)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=config.reports_worksheet_name, rows=100, cols=4
        )
        worksheet.append_row(["period_start", "period_end", "generated_at", "text"])
    return ReportsRowsGateway(worksheet)


def list_leads(gateway) -> list:
    column_a = gateway.get_column(1)
    name_row = find_row_by_label(column_a, FIELD_ROW_LABELS["name"])
    contact_row = find_row_by_label(column_a, FIELD_ROW_LABELS["contact"])

    last_column = gateway.last_used_column()
    leads = []
    for col in range(FIRST_LEAD_COLUMN, last_column + 1):
        column_values = gateway.get_column(col)
        name = column_values[name_row - 1] if len(column_values) >= name_row else ""
        if not name:
            continue
        contact = column_values[contact_row - 1] if len(column_values) >= contact_row else ""
        leads.append({"column": col, "name": name, "contact": contact})
    return leads


def find_lead(gateway, query: str):
    return match_lead(query, list_leads(gateway))


def get_lead(gateway, column: int) -> dict:
    column_a = gateway.get_column(1)
    column_values = gateway.get_column(column)
    result = {}
    for field_name, label in FIELD_ROW_LABELS.items():
        try:
            row = find_row_by_label(column_a, label)
        except RowLabelNotFound:
            continue
        result[field_name] = column_values[row - 1] if len(column_values) >= row else ""
    return result


def create_lead(gateway, name: str, contact: str, manager: str) -> int:
    new_column = gateway.last_used_column() + 1
    column_a = gateway.get_column(1)

    gateway.update_cell(find_row_by_label(column_a, FIELD_ROW_LABELS["name"]), new_column, name)
    gateway.update_cell(find_row_by_label(column_a, FIELD_ROW_LABELS["contact"]), new_column, contact)
    gateway.update_cell(find_row_by_label(column_a, FIELD_ROW_LABELS["manager"]), new_column, manager)
    return new_column


def write_field(gateway, column: int, field_name: str, value: str) -> None:
    if field_name == "status":
        validate_status(value)

    label = FIELD_ROW_LABELS[field_name]
    column_a = gateway.get_column(1)
    row = find_row_by_label(column_a, label)
    gateway.update_cell(row, column, value)


def append_history(gateway, column: int, line: str) -> None:
    column_a = gateway.get_column(1)
    row = find_row_by_label(column_a, FIELD_ROW_LABELS["history"])
    column_values = gateway.get_column(column)
    existing = column_values[row - 1] if len(column_values) >= row else ""
    new_value = f"{existing}\n{line}" if existing else line
    gateway.update_cell(row, column, new_value)


def ensure_schema(gateway) -> None:
    column_a = gateway.get_column(1)
    next_row = len(column_a) + 1
    for label in NEW_BLOCK_LABELS:
        if label in column_a:
            continue
        gateway.update_cell(next_row, 1, label)
        column_a.append(label)
        next_row += 1


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-leads")

    find_parser = subparsers.add_parser("find-lead")
    find_parser.add_argument("--query", required=True)

    get_parser = subparsers.add_parser("get-lead")
    get_parser.add_argument("--column", type=int, required=True)

    create_parser = subparsers.add_parser("create-lead")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--contact", required=True)
    create_parser.add_argument("--manager", required=True)

    write_parser = subparsers.add_parser("write-field")
    write_parser.add_argument("--column", type=int, required=True)
    write_parser.add_argument("--field", required=True)
    write_parser.add_argument("--value", required=True)

    history_parser = subparsers.add_parser("append-history")
    history_parser.add_argument("--column", type=int, required=True)
    history_parser.add_argument("--line", required=True)

    subparsers.add_parser("ensure-schema")

    append_report_parser = subparsers.add_parser("append-report")
    append_report_parser.add_argument("--period-start", required=True)
    append_report_parser.add_argument("--period-end", required=True)
    append_report_parser.add_argument("--generated-at", required=True)
    append_report_parser.add_argument("--text", required=True)

    subparsers.add_parser("list-reports")

    find_report_parser = subparsers.add_parser("find-report")
    find_report_parser.add_argument("--period-start", required=True)
    find_report_parser.add_argument("--period-end", required=True)

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "append-report":
        reports_gateway = open_reports_gateway(config)
        append_report(reports_gateway, args.period_start, args.period_end, args.generated_at, args.text)
        print(json.dumps({"ok": True}, ensure_ascii=False))
        return
    if args.command == "list-reports":
        reports_gateway = open_reports_gateway(config)
        print(json.dumps(list_reports(reports_gateway), ensure_ascii=False))
        return
    if args.command == "find-report":
        reports_gateway = open_reports_gateway(config)
        reports = list_reports(reports_gateway)
        found = find_report_for_period(reports, args.period_start, args.period_end)
        print(json.dumps(found, ensure_ascii=False))
        return

    gateway = open_gateway(config)

    if args.command == "list-leads":
        print(json.dumps(list_leads(gateway), ensure_ascii=False))
    elif args.command == "find-lead":
        result = find_lead(gateway, args.query)
        print(json.dumps({"kind": result.kind, "leads": result.leads}, ensure_ascii=False))
    elif args.command == "get-lead":
        print(json.dumps(get_lead(gateway, args.column), ensure_ascii=False))
    elif args.command == "create-lead":
        column = create_lead(gateway, args.name, args.contact, args.manager)
        print(json.dumps({"column": column}, ensure_ascii=False))
    elif args.command == "write-field":
        write_field(gateway, args.column, args.field, args.value)
        print(json.dumps({"ok": True}, ensure_ascii=False))
    elif args.command == "append-history":
        append_history(gateway, args.column, args.line)
        print(json.dumps({"ok": True}, ensure_ascii=False))
    elif args.command == "ensure-schema":
        ensure_schema(gateway)
        print(json.dumps({"ok": True}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(_main())
