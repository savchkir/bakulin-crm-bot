from dataclasses import dataclass
import re


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = text.lstrip("@")
    text = re.sub(r"\s+", " ", text)
    return text


@dataclass
class MatchResult:
    kind: str  # "exact" | "ambiguous" | "none"
    leads: list


def match_lead(query: str, leads: list) -> MatchResult:
    normalized_query = normalize(query)

    exact = [
        lead
        for lead in leads
        if normalize(lead["contact"]) == normalized_query
        or normalize(lead["name"]) == normalized_query
    ]

    partial = [
        lead
        for lead in leads
        if normalized_query in normalize(lead["name"])
        or normalized_query in normalize(lead["contact"])
    ]

    # Combine exact and partial matches, avoiding duplicates
    seen = set()
    all_matches = []
    for lead in exact + partial:
        lead_id = id(lead)
        if lead_id not in seen:
            all_matches.append(lead)
            seen.add(lead_id)

    if len(all_matches) == 1:
        return MatchResult(kind="exact", leads=all_matches)
    if len(all_matches) > 1:
        return MatchResult(kind="ambiguous", leads=all_matches)

    return MatchResult(kind="none", leads=[])
