import textwrap
import pytest
from crm_bot.config import load_config, ConfigError


def test_load_config_reads_all_fields(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(textwrap.dedent("""
        telegram_bot_token: "abc"
        kirill_chat_id: 111
        partners_group_chat_id: -222
        google_service_account_json: "sa.json"
        sheet_id: "sheet123"
        sheet_worksheet_name: "Ліди"
        reports_worksheet_name: "Звіти"
        calendar_id: "primary"
        calendar_keywords: ["бакулин", "bakulin"]
    """))

    config = load_config(str(config_path))

    assert config.telegram_bot_token == "abc"
    assert config.kirill_chat_id == 111
    assert config.partners_group_chat_id == -222
    assert config.sheet_id == "sheet123"
    assert config.reports_worksheet_name == "Звіти"
    assert config.calendar_keywords == ["бакулин", "bakulin"]


def test_load_config_missing_field_raises(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text('telegram_bot_token: "abc"\n')

    with pytest.raises(ConfigError, match="kirill_chat_id"):
        load_config(str(config_path))
