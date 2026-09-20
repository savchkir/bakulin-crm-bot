from unittest.mock import MagicMock
from crm_bot.calendar_client import list_events

FAKE_API_EVENTS = {
    "items": [
        {"summary": "Олег Бакулин кол", "start": {"dateTime": "2026-09-15T12:00:00+03:00"}},
        {"summary": "Стоматолог", "start": {"dateTime": "2026-09-16T10:00:00+03:00"}},
    ]
}


def test_list_events_filters_by_keyword():
    fake_service = MagicMock()
    fake_service.events().list().execute.return_value = FAKE_API_EVENTS

    events = list_events(
        service=fake_service,
        calendar_id="primary",
        time_min="2026-09-14T00:00:00Z",
        time_max="2026-09-20T00:00:00Z",
        keywords=["бакулин"],
    )

    assert len(events) == 1
    assert events[0]["summary"] == "Олег Бакулин кол"
