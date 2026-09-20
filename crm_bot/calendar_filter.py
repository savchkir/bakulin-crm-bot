def filter_events_by_keywords(events: list, keywords: list) -> list:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    matched = []
    for event in events:
        summary = event.get("summary", "").lower()
        if any(keyword in summary for keyword in lowered_keywords):
            matched.append(event)
    return matched
