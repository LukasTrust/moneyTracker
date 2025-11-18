from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError


from app.schemas.category import (
    CategoryMappings,
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)


def test_category_mappings_defaults_and_values():
    m = CategoryMappings()
    assert isinstance(m.patterns, list)
    assert m.patterns == []

    m2 = CategoryMappings(patterns=["rent", "subscription"])
    assert m2.patterns == ["rent", "subscription"]


def test_category_base_valid_and_defaults():
    cb = CategoryBase(name="Groceries", color="#FFAABB")
    assert cb.name == "Groceries"
    assert cb.color.upper() == "#FFAABB"
    # icon optional defaults to None
    assert cb.icon is None
    # mappings default provided
    assert isinstance(cb.mappings, CategoryMappings)


@pytest.mark.parametrize("bad_name", [""])
def test_category_base_invalid_name(bad_name):
    with pytest.raises(ValidationError):
        CategoryBase(name=bad_name, color="#000000")


def test_color_validation_rejects_bad_values():
    with pytest.raises(ValidationError):
        CategoryBase(name="x", color="red")

    with pytest.raises(ValidationError):
        CategoryBase(name="x", color="#GGGGGG")


def test_icon_length_validation():
    # icon must be <= 10 chars
    ok_icon = "😊"
    cb = CategoryBase(name="X", color="#123456", icon=ok_icon)
    assert cb.icon == ok_icon

    long_icon = "a" * 11
    with pytest.raises(ValidationError):
        CategoryBase(name="X", color="#123456", icon=long_icon)


def test_category_update_allows_partial_and_mappings_none():
    cu = CategoryUpdate()
    assert cu.name is None and cu.color is None and cu.mappings is None

    cu2 = CategoryUpdate(name="New", mappings=CategoryMappings(patterns=["a"]))
    assert cu2.name == "New"
    assert isinstance(cu2.mappings, CategoryMappings)


def test_category_response_fields_and_types():
    now = datetime.utcnow()
    resp = CategoryResponse(
        id=5,
        name="Test",
        color="#abcdef",
        created_at=now,
        updated_at=now + timedelta(seconds=1),
    )

    assert resp.id == 5
    assert resp.created_at == now
    assert resp.updated_at > resp.created_at
    assert resp.name == "Test"
