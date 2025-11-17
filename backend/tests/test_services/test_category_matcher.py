from types import SimpleNamespace
from app.services.category_matcher import CategoryMatcher


class FakeQuery:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeDB:
    def __init__(self, items):
        self._items = items

    def query(self, model):
        return FakeQuery(self._items)


def test_match_category_by_recipient():
    # Create fake categories with patterns
    cat1 = SimpleNamespace(id=1, mappings={'patterns': ['REWE', 'EDEKA']})
    cat2 = SimpleNamespace(id=2, mappings={'patterns': ['Miete']})

    db = FakeDB([cat1, cat2])
    matcher = CategoryMatcher(db)

    tid = matcher.match_category({'recipient': 'REWE Markt', 'purpose': ''})
    assert tid == 1


def test_no_match_returns_none():
    cat = SimpleNamespace(id=1, mappings={'patterns': ['XYZ']})
    db = FakeDB([cat])
    matcher = CategoryMatcher(db)

    assert matcher.match_category({'recipient': 'Unknown', 'purpose': 'something'}) is None
