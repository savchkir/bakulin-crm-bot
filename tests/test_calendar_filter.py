from crm_bot.calendar_filter import filter_events_by_keywords

EVENTS = [
    {"summary": "Олег Бакулин кол", "start": "2026-09-15T12:00:00"},
    {"summary": "Стоматолог", "start": "2026-09-16T10:00:00"},
    {"summary": "Бакулін созвон", "start": "2026-09-17T09:00:00"},
    {"summary": "Sync with Bakulin team", "start": "2026-09-18T14:00:00"},
]


def test_filters_case_and_language_insensitively():
    result = filter_events_by_keywords(EVENTS, ["бакулин", "бакулін", "bakulin"])
    summaries = {event["summary"] for event in result}
    assert summaries == {
        "Олег Бакулин кол",
        "Бакулін созвон",
        "Sync with Bakulin team",
    }


def test_excludes_non_matching_events():
    result = filter_events_by_keywords(EVENTS, ["бакулин", "бакулін", "bakulin"])
    assert "Стоматолог" not in {event["summary"] for event in result}


def test_handles_missing_summary_gracefully():
    events = [{"start": "2026-09-15T12:00:00"}]
    assert filter_events_by_keywords(events, ["бакулин"]) == []
