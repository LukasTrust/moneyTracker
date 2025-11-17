from types import SimpleNamespace
from datetime import date

from app.services.transfer_matcher import TransferMatcher
from app.models.transfer import Transfer
from app.models.data_row import DataRow


class FakeQuery:
    def __init__(self, items):
        self._items = list(items)
        self._last_filtered = None

    def filter(self, condition):
        # Try to extract a direct value from binary expressions (left == value)
        try:
            val = getattr(condition, 'right').value
        except Exception:
            val = None
        self._last_filtered = val
        return self

    def first(self):
        if self._last_filtered is None:
            return None
        for it in self._items:
            if getattr(it, 'id', None) == self._last_filtered:
                return it
            if getattr(it, 'from_transaction_id', None) == self._last_filtered:
                return it
            if getattr(it, 'to_transaction_id', None) == self._last_filtered:
                return it
        return None

    def all(self):
        return list(self._items)


class FakeDB:
    def __init__(self, data_rows=None, transfers=None):
        self._data_rows = list(data_rows or [])
        self._transfers = list(transfers or [])
        self._pending = []

    def query(self, model):
        name = getattr(model, '__name__', '')
        if name == 'DataRow':
            return FakeQuery(self._data_rows)
        if name == 'Transfer':
            return FakeQuery(self._transfers)
        return FakeQuery([])

    def add(self, obj):
        # Simulate DB assigning a new id
        obj.id = len(self._transfers) + len(self._pending) + 1
        self._pending.append(obj)

    def commit(self):
        # Commit pending transfers into stored transfers
        self._transfers.extend(self._pending)
        self._pending = []

    def refresh(self, obj):
        # No-op for the fake DB
        return obj


def make_tx(id, account_id, amount, tx_date, recipient=None, purpose=None):
    return SimpleNamespace(
        id=id,
        account_id=account_id,
        amount=amount,
        transaction_date=tx_date,
        recipient=recipient,
        purpose=purpose,
        category_id=None,
    )


def test_create_transfer_success():
    from_tx = make_tx(1, 1, -50, date(2025, 1, 1), recipient='A')
    to_tx = make_tx(2, 2, 50, date(2025, 1, 2), recipient='A')

    db = FakeDB(data_rows=[from_tx, to_tx], transfers=[])
    matcher = TransferMatcher(db=db)

    transfer = matcher.create_transfer(1, 2, is_auto_detected=True, confidence_score=0.9, notes='test')

    # Should return a Transfer-like object and be stored in fake DB
    assert hasattr(transfer, 'id')
    # Amount should equal absolute of from_tx
    assert float(transfer.amount) == 50.0
    assert transfer.is_auto_detected
    assert float(transfer.confidence_score) == 0.9


def test_create_transfer_invalid_amounts_raises():
    from_tx = make_tx(1, 1, 50, date(2025, 1, 1))
    to_tx = make_tx(2, 2, 50, date(2025, 1, 2))

    db = FakeDB(data_rows=[from_tx, to_tx], transfers=[])
    matcher = TransferMatcher(db=db)

    try:
        matcher.create_transfer(1, 2)
        assert False, "Expected ValueError for invalid transfer amounts"
    except ValueError as e:
        assert 'from_transaction must be negative' in str(e) or 'Invalid transfer' in str(e)
