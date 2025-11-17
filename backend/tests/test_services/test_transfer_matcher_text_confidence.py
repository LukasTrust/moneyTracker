from types import SimpleNamespace
from datetime import date

from app.services.transfer_matcher import TransferMatcher


def make_tx(id, account_id, amount, tx_date, recipient=None, purpose=None, category_id=None):
    return SimpleNamespace(
        id=id,
        account_id=account_id,
        amount=amount,
        transaction_date=tx_date,
        recipient=recipient,
        purpose=purpose,
        category_id=category_id,
    )


def test_text_similarity_full_and_partial():
    tx1 = make_tx(1, 1, -10, date(2025, 1, 1), recipient="REWE Markt", purpose="Einkauf Lebensmittel")
    tx2 = make_tx(2, 2, 10, date(2025, 1, 1), recipient="REWE", purpose="Lebensmittel Einkauf")

    matcher = TransferMatcher(db=None)

    # Words overlap: 'rewe' and 'lebensmittel' -> some positive similarity
    sim = matcher._calculate_text_similarity(tx1, tx2)
    assert 0.0 < sim <= 1.0

    # Identical descriptions => similarity == 1.0
    tx3 = make_tx(3, 3, 10, date(2025, 1, 1), recipient="Same", purpose="Exact Match")
    tx4 = make_tx(4, 4, -10, date(2025, 1, 1), recipient="Same", purpose="Exact Match")
    assert matcher._calculate_text_similarity(tx3, tx4) == 1.0


def test_calculate_confidence_date_and_text_bonus():
    matcher = TransferMatcher(db=None)

    base_tx = make_tx(1, 1, -100, date(2025, 1, 1), recipient="Alice", purpose="Transfer")
    same_day_tx = make_tx(2, 2, 100, date(2025, 1, 1), recipient="Alice", purpose="Transfer")
    three_days_tx = make_tx(3, 2, 100, date(2025, 1, 4), recipient="Alice", purpose="Transfer")
    no_text_tx = make_tx(4, 2, 100, date(2025, 1, 1), recipient=None, purpose=None)

    # Same day -> should include same day bonus (higher score)
    c_same = matcher._calculate_confidence(base_tx, same_day_tx, date_diff=0)
    c_three = matcher._calculate_confidence(base_tx, three_days_tx, date_diff=3)
    assert c_same >= c_three

    # No text -> text bonus 0 but date proximity still counts
    c_no_text = matcher._calculate_confidence(base_tx, no_text_tx, date_diff=0)
    assert isinstance(c_no_text, float)
    assert 0.0 <= c_no_text <= 1.0
