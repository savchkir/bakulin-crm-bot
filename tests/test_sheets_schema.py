import pytest
from crm_bot.sheets_schema import (
    STATUS_OPTIONS,
    validate_status,
    FIELD_ROW_LABELS,
    find_row_by_label,
    RowLabelNotFound,
)


def test_status_options_match_agreed_list():
    assert STATUS_OPTIONS == [
        "Назначаем созвон",
        "Ожидаем решение",
        "Ожидаем оплату",
        "Частичная оплата",
        "Оплатил",
        "Отказ",
        "Догрев",
    ]


def test_validate_status_accepts_known_value():
    validate_status("Оплатил")  # must not raise


def test_validate_status_rejects_unknown_value():
    with pytest.raises(ValueError, match="Оплачено"):
        validate_status("Оплачено")


def test_find_row_by_label_returns_1_indexed_row():
    column_a = ["Лід №", "Дата дзвінка", "Ім'я", "Контакт / нік", "Менеджер"]
    assert find_row_by_label(column_a, FIELD_ROW_LABELS["name"]) == 3


def test_find_row_by_label_raises_when_missing():
    column_a = ["Лід №", "Дата дзвінка"]
    with pytest.raises(RowLabelNotFound, match="Ім'я"):
        find_row_by_label(column_a, FIELD_ROW_LABELS["name"])
