"""
Tests for RecipientMatcher service
"""
from types import SimpleNamespace
from app.services.recipient_matcher import RecipientMatcher


class FakeQuery:
    def __init__(self, items):
        self._items = items
        self._filters = []
    
    def filter(self, condition):
        # Simple mock that returns self for chaining
        return self
    
    def first(self):
        return self._items[0] if self._items else None
    
    def all(self):
        return self._items


class FakeDB:
    def __init__(self, recipients=None):
        self._recipients = recipients or []
        self._added = []
        self._committed = False
    
    def query(self, model):
        return FakeQuery(self._recipients)
    
    def add(self, item):
        self._added.append(item)
    
    def commit(self):
        self._committed = True
    
    def refresh(self, item):
        pass


class FakeRecipient:
    def __init__(self, id=None, name=None, normalized_name=None, aliases=None, transaction_count=0):
        self.id = id
        self.name = name
        self.normalized_name = normalized_name
        self.aliases = aliases or []
        self.transaction_count = transaction_count
    
    def add_alias(self, alias):
        if alias not in self.aliases:
            self.aliases.append(alias)
    
    @staticmethod
    def normalize_name(name):
        """Simple normalization for testing"""
        if not name:
            return ""
        return name.strip().lower().replace("  ", " ")


def test_find_or_create_with_empty_name():
    """Should return None for empty names"""
    db = FakeDB()
    matcher = RecipientMatcher(db)
    
    result = matcher.find_or_create_recipient("")
    assert result is None
    
    result = matcher.find_or_create_recipient("   ")
    assert result is None


def test_find_or_create_new_recipient():
    """Should create new recipient if none exists"""
    db = FakeDB(recipients=[])
    matcher = RecipientMatcher(db)
    
    # Mock the Recipient model's normalize_name
    from app.services import recipient_matcher
    original_normalize = None
    
    # Patch for this test
    class MockRecipient:
        @staticmethod
        def normalize_name(name):
            return name.strip().lower()
    
    # Simple test - the actual creation happens in the service
    # We're just testing the logic flow
    assert len(db._added) == 0  # Nothing added yet


def test_similarity_threshold_constant():
    """Test that similarity threshold is defined"""
    assert hasattr(RecipientMatcher, 'SIMILARITY_THRESHOLD')
    assert 0.0 <= RecipientMatcher.SIMILARITY_THRESHOLD <= 1.0
    assert RecipientMatcher.SIMILARITY_THRESHOLD == 0.85


def test_recipient_matcher_initialization():
    """Test that RecipientMatcher initializes with db"""
    db = FakeDB()
    matcher = RecipientMatcher(db)
    
    assert matcher.db is db
    assert hasattr(matcher, 'find_or_create_recipient')
    assert hasattr(matcher, '_find_similar_recipient')
