from app.services.data_aggregator import DataAggregator


def test_parse_amount_various_formats():
    assert DataAggregator.parse_amount('-50,00') == -50.0
    assert DataAggregator.parse_amount('€1.234,56') == 1234.56
    assert DataAggregator.parse_amount('') == 0.0
    assert DataAggregator.parse_amount('bad') == 0.0
