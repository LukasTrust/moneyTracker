from app.services.hash_service import HashService


def test_generate_hash_is_deterministic():
    data = {"date": "2024-11-15", "amount": "-42.50", "recipient": "REWE"}
    h1 = HashService.generate_hash(data)
    h2 = HashService.generate_hash(data.copy())
    assert isinstance(h1, str) and len(h1) == 64
    assert h1 == h2


def test_is_duplicate():
    data = {"a": 1}
    h = HashService.generate_hash(data)
    existing = {h}
    assert HashService.is_duplicate(h, existing)
    assert not HashService.is_duplicate('deadbeef', existing)
