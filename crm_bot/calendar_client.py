import argparse
import json
import sys

from crm_bot.config import load_config
from crm_bot.calendar_filter import filter_events_by_keywords


def build_service(config):
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    credentials = Credentials.from_service_account_file(
        config.google_service_account_json, scopes=scopes
    )
    return build("calendar", "v3", credentials=credentials)


def list_events(service, calendar_id: str, time_min: str, time_max: str, keywords: list) -> list:
    response = (
        service.events()
        .list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True)
        .execute()
    )
    return filter_events_by_keywords(response.get("items", []), keywords)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-events")
    list_parser.add_argument("--start", required=True, help="ISO 8601, e.g. 2026-09-14T00:00:00Z")
    list_parser.add_argument("--end", required=True, help="ISO 8601, e.g. 2026-09-20T00:00:00Z")

    args = parser.parse_args()
    config = load_config(args.config)
    service = build_service(config)

    if args.command == "list-events":
        events = list_events(service, config.calendar_id, args.start, args.end, config.calendar_keywords)
        print(json.dumps(events, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(_main())
