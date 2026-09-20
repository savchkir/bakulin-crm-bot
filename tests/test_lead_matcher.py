from crm_bot.lead_matcher import match_lead, MatchResult

LEADS = [
    {"column": "C", "name": "Олег", "contact": "@oleg_lawyer"},
    {"column": "D", "name": "Олена Петренко", "contact": "@olena_p"},
    {"column": "E", "name": "Олег Ткаченко", "contact": "@oleg_tk"},
]


def test_exact_contact_match():
    result = match_lead("@oleg_lawyer", LEADS)
    assert result.kind == "exact"
    assert result.leads[0]["column"] == "C"


def test_exact_name_match_case_insensitive():
    result = match_lead("олена петренко", LEADS)
    assert result.kind == "exact"
    assert result.leads[0]["column"] == "D"


def test_ambiguous_when_name_matches_multiple_leads():
    result = match_lead("олег", LEADS)
    assert result.kind == "ambiguous"
    columns = {lead["column"] for lead in result.leads}
    assert columns == {"C", "E"}


def test_none_when_nothing_close():
    result = match_lead("Ірина Коваль", LEADS)
    assert result.kind == "none"
    assert result.leads == []
