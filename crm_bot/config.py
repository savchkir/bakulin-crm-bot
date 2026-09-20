from dataclasses import dataclass
import yaml

REQUIRED_FIELDS = [
    "telegram_bot_token",
    "kirill_chat_id",
    "partners_group_chat_id",
    "google_service_account_json",
    "sheet_id",
    "sheet_worksheet_name",
    "reports_worksheet_name",
    "calendar_id",
    "calendar_keywords",
]


class ConfigError(Exception):
    pass


@dataclass
class Config:
    telegram_bot_token: str
    kirill_chat_id: int
    partners_group_chat_id: int
    google_service_account_json: str
    sheet_id: str
    sheet_worksheet_name: str
    reports_worksheet_name: str
    calendar_id: str
    calendar_keywords: list
    telegram_relay_url: str = None
    telegram_relay_secret: str = None


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ConfigError(f"config.yaml is missing required field(s): {', '.join(missing)}")

    fields = {field: raw[field] for field in REQUIRED_FIELDS}
    fields["telegram_relay_url"] = raw.get("telegram_relay_url")
    fields["telegram_relay_secret"] = raw.get("telegram_relay_secret")
    return Config(**fields)
