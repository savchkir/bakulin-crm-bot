import argparse
import json
import sys
import requests

from crm_bot.config import load_config

API_BASE = "https://api.telegram.org"


def get_updates(token: str, offset: int = None, relay_url: str = None, relay_secret: str = None) -> list:
    params = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset
    if relay_url:
        relay_payload = {
            "secret": relay_secret,
            "token": token,
            "method": "getUpdates",
            "httpMethod": "get",
            "params": params,
        }
        response = requests.post(relay_url, json=relay_payload)
        return response.json().get("result", [])
    response = requests.get(f"{API_BASE}/bot{token}/getUpdates", params=params)
    return response.json().get("result", [])


def send_message(
    token: str, chat_id: int, text: str, thread_id: int = None, relay_url: str = None, relay_secret: str = None
) -> dict:
    payload = {"chat_id": chat_id, "text": text}
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    if relay_url:
        relay_payload = {
            "secret": relay_secret,
            "token": token,
            "method": "sendMessage",
            "httpMethod": "post",
            "params": payload,
        }
        response = requests.post(relay_url, json=relay_payload)
        return response.json().get("result", {})
    response = requests.post(f"{API_BASE}/bot{token}/sendMessage", json=payload)
    return response.json().get("result", {})


def resolve_chat_id(raw_value: str, config) -> int:
    """Accepts a raw numeric chat id, or the convenience keywords 'kirill' / 'partners'
    which resolve to config.kirill_chat_id / config.partners_group_chat_id."""
    if raw_value == "kirill":
        return config.kirill_chat_id
    if raw_value == "partners":
        return config.partners_group_chat_id
    return int(raw_value)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--token", default=None, help="Overrides telegram_bot_token from --config")
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_updates_parser = subparsers.add_parser("get-updates")
    get_updates_parser.add_argument("--offset", type=int, default=None)

    send_parser = subparsers.add_parser("send")
    send_parser.add_argument(
        "--chat-id", required=True, help="A numeric chat id, or 'kirill' / 'partners'"
    )
    send_parser.add_argument("--text", required=True)
    send_parser.add_argument(
        "--thread-id", type=int, default=None, help="Forum topic id, e.g. 16 for 'Общение с ботом'"
    )

    args = parser.parse_args()
    config = load_config(args.config)
    token = args.token or config.telegram_bot_token
    relay_url = config.telegram_relay_url
    relay_secret = config.telegram_relay_secret

    if args.command == "get-updates":
        result = get_updates(token, args.offset, relay_url=relay_url, relay_secret=relay_secret)
        print(json.dumps(result, ensure_ascii=False))
    elif args.command == "send":
        chat_id = resolve_chat_id(args.chat_id, config)
        result = send_message(
            token, chat_id, args.text, args.thread_id, relay_url=relay_url, relay_secret=relay_secret
        )
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(_main())
