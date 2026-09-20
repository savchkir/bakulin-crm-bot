# bakulin-crm-bot/crm_bot/sheets_schema.py

STATUS_OPTIONS = [
    "Назначаем созвон",
    "Ожидаем решение",
    "Ожидаем оплату",
    "Частичная оплата",
    "Оплатил",
    "Отказ",
    "Догрев",
]

# Logical field name -> exact label text as it appears in column A of the sheet.
FIELD_ROW_LABELS = {
    "lead_number": "Лід №",
    "call_date": "Дата дзвінка",
    "name": "Ім'я",
    "contact": "Контакт / нік",
    "manager": "Менеджер",
    "manager_comment": "Коментар менеджера",
    "status": "Поточний статус",
    "last_contact_date": "Дата останнього контакту",
    "next_contact_date": "Дата наступного контакту",
    "amount": "Сума / чек",
    "installment": "Розстрочка (так/ні)",
    "payment_screenshot": "Скриншот оплати",
    "history": "Історія оновлень",
}

# Labels that belong to the new block this project adds under "Коментар менеджера",
# in the order they should be appended if missing. Used by sheets_client.ensure_schema.
NEW_BLOCK_LABELS = [
    "ОНОВЛЕННЯ ПО УГОДІ",
    FIELD_ROW_LABELS["status"],
    FIELD_ROW_LABELS["last_contact_date"],
    FIELD_ROW_LABELS["next_contact_date"],
    FIELD_ROW_LABELS["amount"],
    FIELD_ROW_LABELS["installment"],
    FIELD_ROW_LABELS["payment_screenshot"],
    FIELD_ROW_LABELS["history"],
]


class RowLabelNotFound(Exception):
    pass


def validate_status(value: str) -> None:
    if value not in STATUS_OPTIONS:
        raise ValueError(
            f"Unknown status '{value}'. Allowed values: {', '.join(STATUS_OPTIONS)}"
        )


def find_row_by_label(column_a_values: list, label: str) -> int:
    for index, cell_value in enumerate(column_a_values, start=1):
        if cell_value == label:
            return index
    raise RowLabelNotFound(f"Label '{label}' not found in column A")
