from unittest.mock import patch, MagicMock
from crm_bot.telegram_client import get_updates, send_message, resolve_chat_id


@patch("crm_bot.telegram_client.requests.get")
def test_get_updates_calls_correct_url_and_returns_result(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "ok": True,
        "result": [{"update_id": 5, "message": {"text": "hi"}}],
    }
    mock_get.return_value = mock_response

    updates = get_updates(token="TOKEN", offset=3)

    called_url = mock_get.call_args[0][0]
    assert "botTOKEN/getUpdates" in called_url
    assert mock_get.call_args[1]["params"]["offset"] == 3
    assert updates == [{"update_id": 5, "message": {"text": "hi"}}]


@patch("crm_bot.telegram_client.requests.post")
def test_send_message_posts_text_to_chat(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 42}}
    mock_post.return_value = mock_response

    result = send_message(token="TOKEN", chat_id=111, text="Записал: Олег")

    called_url = mock_post.call_args[0][0]
    assert "botTOKEN/sendMessage" in called_url
    assert mock_post.call_args[1]["json"] == {"chat_id": 111, "text": "Записал: Олег"}
    assert result == {"message_id": 42}


@patch("crm_bot.telegram_client.requests.post")
def test_send_message_includes_thread_id_when_given(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 43}}
    mock_post.return_value = mock_response

    send_message(token="TOKEN", chat_id=-222, text="Как дела?", thread_id=16)

    assert mock_post.call_args[1]["json"] == {
        "chat_id": -222,
        "text": "Как дела?",
        "message_thread_id": 16,
    }


@patch("crm_bot.telegram_client.requests.post")
def test_send_message_omits_thread_id_when_not_given(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 44}}
    mock_post.return_value = mock_response

    send_message(token="TOKEN", chat_id=111, text="Привет")

    assert "message_thread_id" not in mock_post.call_args[1]["json"]


@patch("crm_bot.telegram_client.requests.post")
def test_get_updates_uses_relay_when_configured(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": [{"update_id": 9}]}
    mock_post.return_value = mock_response

    updates = get_updates(
        token="TOKEN", offset=3, relay_url="https://script.google.com/relay", relay_secret="s3cr3t"
    )

    called_url = mock_post.call_args[0][0]
    sent_json = mock_post.call_args[1]["json"]
    assert called_url == "https://script.google.com/relay"
    assert sent_json["secret"] == "s3cr3t"
    assert sent_json["token"] == "TOKEN"
    assert sent_json["method"] == "getUpdates"
    assert sent_json["params"]["offset"] == 3
    assert updates == [{"update_id": 9}]


@patch("crm_bot.telegram_client.requests.post")
def test_send_message_uses_relay_when_configured(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"message_id": 50}}
    mock_post.return_value = mock_response

    result = send_message(
        token="TOKEN",
        chat_id=111,
        text="Привет",
        relay_url="https://script.google.com/relay",
        relay_secret="s3cr3t",
    )

    called_url = mock_post.call_args[0][0]
    sent_json = mock_post.call_args[1]["json"]
    assert called_url == "https://script.google.com/relay"
    assert sent_json["method"] == "sendMessage"
    assert sent_json["params"] == {"chat_id": 111, "text": "Привет"}
    assert result == {"message_id": 50}


class FakeConfig:
    kirill_chat_id = 111
    partners_group_chat_id = -222


def test_resolve_chat_id_keyword_kirill():
    assert resolve_chat_id("kirill", FakeConfig()) == 111


def test_resolve_chat_id_keyword_partners():
    assert resolve_chat_id("partners", FakeConfig()) == -222


def test_resolve_chat_id_raw_number():
    assert resolve_chat_id("999", FakeConfig()) == 999
