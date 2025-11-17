from app.services.mapping_suggester import MappingSuggester


def test_suggest_mappings_basic_headers():
    headers = ["Buchungstag", "Betrag", "Empfänger", "Verwendungszweck"]
    suggestions = MappingSuggester.suggest_mappings(headers)

    # Expect date and amount to be detected with reasonable confidence
    assert suggestions['date'][0] in headers
    assert suggestions['date'][1] >= 0.7
    assert suggestions['amount'][0] in headers
    assert suggestions['amount'][1] > 0.7


def test_validate_mapping_detects_issues():
    headers = ["Buchungstag", "Betrag"]
    mapping = {"date": "Buchungstag", "amount": "Betrag"}
    ok, errors = MappingSuggester.validate_mapping(mapping, headers, required_fields=['date', 'amount'])
    assert ok and not errors

    # Missing required field
    bad_mapping = {"date": "Buchungstag"}
    ok2, errors2 = MappingSuggester.validate_mapping(bad_mapping, headers)
    assert not ok2
    assert any("Required field" in e for e in errors2)
