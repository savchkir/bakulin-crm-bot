from crm_bot.mailbox import read_unprocessed_updates, queue_outgoing_message, INBOX_HEADERS


class FakeGateway:
    def __init__(self, rows):
        self.rows = rows  # list of lists, including header row
        self.updated_cells = []
        self.appended_rows = []

    def get_all_values(self) -> list:
        return self.rows

    def update_cell(self, row: int, col: int, value: str) -> None:
        self.updated_cells.append((row, col, value))

    def append_row(self, row: list) -> None:
        self.appended_rows.append(row)


def test_read_unprocessed_updates_skips_processed_rows():
    gateway = FakeGateway(
        [
            INBOX_HEADERS,
            ["TRUE", "1", "111", "", "Кирилл", "старое сообщение", "2026-09-20T10:00:00Z"],
            ["FALSE", "2", "111", "16", "Кирилл", "Олег оплатил", "2026-09-20T11:00:00Z"],
        ]
    )

    updates = read_unprocessed_updates(gateway)

    assert len(updates) == 1
    assert updates[0]["update_id"] == 2
    assert updates[0]["message"]["chat"]["id"] == 111
    assert updates[0]["message"]["message_thread_id"] == 16
    assert updates[0]["message"]["text"] == "Олег оплатил"
    assert updates[0]["message"]["from"]["first_name"] == "Кирилл"


def test_read_unprocessed_updates_marks_row_processed():
    gateway = FakeGateway(
        [
            INBOX_HEADERS,
            ["FALSE", "5", "222", "", "Кирилл", "привет", "2026-09-20T11:00:00Z"],
        ]
    )

    read_unprocessed_updates(gateway)

    assert gateway.updated_cells == [(2, 1, "TRUE")]


def test_read_unprocessed_updates_omits_thread_id_when_blank():
    gateway = FakeGateway(
        [
            INBOX_HEADERS,
            ["FALSE", "3", "111", "", "Кирилл", "без темы", "2026-09-20T11:00:00Z"],
        ]
    )

    updates = read_unprocessed_updates(gateway)

    assert "message_thread_id" not in updates[0]["message"]


def test_read_unprocessed_updates_returns_empty_for_no_new_rows():
    gateway = FakeGateway([INBOX_HEADERS])

    assert read_unprocessed_updates(gateway) == []


def test_queue_outgoing_message_appends_unsent_row():
    gateway = FakeGateway([])

    queue_outgoing_message(gateway, 111, "Записал: Олег", thread_id=16)

    assert gateway.appended_rows == [["FALSE", "111", "Записал: Олег", "16", ""]]


def test_queue_outgoing_message_omits_thread_id_when_not_given():
    gateway = FakeGateway([])

    queue_outgoing_message(gateway, 111, "Привет")

    assert gateway.appended_rows == [["FALSE", "111", "Привет", "", ""]]
