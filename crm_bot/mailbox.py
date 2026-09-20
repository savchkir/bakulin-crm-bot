# bakulin-crm-bot/crm_bot/mailbox.py
"""Telegram <-> Google Sheet mailbox: lets the routine talk to Telegram
indirectly through the sheet (googleapis.com, already reachable) instead of
calling api.telegram.org directly (blocked by the routine sandbox's egress
policy). A Google Apps Script running on Google's own servers bridges the
other side: it receives Telegram's webhook into the Inbox tab and drains the
Outbox tab into real Telegram sendMessage calls.
"""

INBOX_HEADERS = ["processed", "update_id", "chat_id", "message_thread_id", "from_name", "text", "received_at"]
OUTBOX_HEADERS = ["sent", "chat_id", "text", "thread_id", "requested_at"]


class SheetRowsGateway:
    """Thin real adapter over gspread.Worksheet. Not covered by unit tests directly —
    exercised only in the manual smoke test in README.md."""

    def __init__(self, worksheet):
        self.worksheet = worksheet

    def get_all_values(self) -> list:
        return self.worksheet.get_all_values()

    def update_cell(self, row: int, col: int, value: str) -> None:
        self.worksheet.update_cell(row, col, value)

    def append_row(self, row: list) -> None:
        self.worksheet.append_row(row)


def _open_worksheet(config, worksheet_name: str, headers: list) -> SheetRowsGateway:
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread.exceptions import WorksheetNotFound

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(config.google_service_account_json, scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(config.sheet_id)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=200, cols=len(headers))
        worksheet.append_row(headers)
    return SheetRowsGateway(worksheet)


def open_inbox_gateway(config) -> SheetRowsGateway:
    return _open_worksheet(config, config.inbox_worksheet_name, INBOX_HEADERS)


def open_outbox_gateway(config) -> SheetRowsGateway:
    return _open_worksheet(config, config.outbox_worksheet_name, OUTBOX_HEADERS)


def read_unprocessed_updates(gateway) -> list:
    """Reads unread rows from the Inbox tab, marks them processed, and returns
    them shaped like Telegram Bot API 'update' objects so callers can treat
    this like a normal getUpdates() response."""
    rows = gateway.get_all_values()
    updates = []
    for sheet_row, row in enumerate(rows[1:], start=2):  # skip header; sheet rows are 1-indexed
        padded = row + [""] * (len(INBOX_HEADERS) - len(row))
        processed, update_id, chat_id, thread_id, from_name, text, _received_at = padded[:7]
        if processed == "TRUE" or not chat_id:
            continue
        message = {
            "chat": {"id": int(chat_id)},
            "from": {"first_name": from_name},
            "text": text,
        }
        if thread_id:
            message["message_thread_id"] = int(thread_id)
        updates.append({"update_id": int(update_id) if update_id else 0, "message": message})
        gateway.update_cell(sheet_row, 1, "TRUE")
    return updates


def queue_outgoing_message(gateway, chat_id, text: str, thread_id: int = None) -> None:
    gateway.append_row(["FALSE", str(chat_id), text, str(thread_id) if thread_id is not None else "", ""])
