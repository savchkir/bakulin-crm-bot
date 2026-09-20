import pytest
from crm_bot.sheets_client import (
    list_leads,
    find_lead,
    get_lead,
    create_lead,
    write_field,
    append_history,
    ensure_schema,
)
from crm_bot.sheets_schema import FIELD_ROW_LABELS


class FakeGateway:
    """In-memory stand-in for the GspreadGateway, 1-indexed rows/cols like gspread."""

    def __init__(self, grid: dict):
        # grid: {(row, col): value}
        self.grid = dict(grid)

    def get_column(self, col: int) -> list:
        max_row = max((r for (r, c) in self.grid if c == col), default=0)
        return [self.grid.get((r, col), "") for r in range(1, max_row + 1)]

    def last_used_column(self) -> int:
        return max((c for (_, c) in self.grid), default=1)

    def update_cell(self, row: int, col: int, value: str) -> None:
        self.grid[(row, col)] = value

    def append_column_at(self, col: int) -> None:
        pass  # no-op for the fake; writing cells beyond current max just extends it


def base_grid():
    column_a = [
        "Лід №", "Дата дзвінка", "Ім'я", "Контакт / нік", "Менеджер",
        "", "ПИТАННЯ",
    ]
    grid = {(row, 1): label for row, label in enumerate(column_a, start=1)}
    # one existing lead in column 3 (C)
    grid[(1, 3)] = "1"
    grid[(2, 3)] = "12.09, 15:00"
    grid[(3, 3)] = "Олег"
    grid[(4, 3)] = "@oleg_lawyer"
    grid[(5, 3)] = "Ірина"
    return grid


def test_list_leads_reads_name_and_contact():
    gateway = FakeGateway(base_grid())
    leads = list_leads(gateway)
    assert leads == [{"column": 3, "name": "Олег", "contact": "@oleg_lawyer"}]


def test_find_lead_delegates_to_matcher():
    gateway = FakeGateway(base_grid())
    result = find_lead(gateway, "олег")
    assert result.kind == "exact"
    assert result.leads[0]["column"] == 3


def test_create_lead_writes_header_in_next_column():
    gateway = FakeGateway(base_grid())
    new_column = create_lead(gateway, name="Ірина Коваль", contact="@irk", manager="Ірина")
    assert new_column == 4
    assert gateway.grid[(3, 4)] == "Ірина Коваль"
    assert gateway.grid[(4, 4)] == "@irk"
    assert gateway.grid[(5, 4)] == "Ірина"


def test_write_field_validates_status():
    gateway = FakeGateway(base_grid())
    with pytest.raises(ValueError, match="Оплачено"):
        write_field(gateway, column=3, field_name="status", value="Оплачено")


def test_write_field_writes_known_field():
    grid = base_grid()
    grid[(8, 1)] = FIELD_ROW_LABELS["status"]
    gateway = FakeGateway(grid)
    write_field(gateway, column=3, field_name="status", value="Оплатил")
    assert gateway.grid[(8, 3)] == "Оплатил"


def test_append_history_adds_new_line_without_losing_old_ones():
    grid = base_grid()
    grid[(9, 1)] = FIELD_ROW_LABELS["history"]
    grid[(9, 3)] = "[10.09] Первый созвон"
    gateway = FakeGateway(grid)
    append_history(gateway, column=3, line="[13.09] Думает, перезвон 20.09")
    assert gateway.grid[(9, 3)] == "[10.09] Первый созвон\n[13.09] Думает, перезвон 20.09"


def test_ensure_schema_adds_missing_new_block_labels():
    gateway = FakeGateway(base_grid())
    ensure_schema(gateway)
    column_a = gateway.get_column(1)
    assert FIELD_ROW_LABELS["status"] in column_a
    assert FIELD_ROW_LABELS["history"] in column_a


def test_ensure_schema_is_idempotent():
    gateway = FakeGateway(base_grid())
    ensure_schema(gateway)
    length_after_first = len(gateway.get_column(1))
    ensure_schema(gateway)
    assert len(gateway.get_column(1)) == length_after_first
