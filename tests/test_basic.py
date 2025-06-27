"""
Basic tests to ensure the test suite runs
"""


def test_always_passes():
    """A test that always passes to ensure pytest works"""
    assert 1 + 1 == 2


def test_string_operations():
    """Test basic string operations"""
    text = "MUED Snowflake AI App"
    assert text.lower() == "mued snowflake ai app"
    assert "Snowflake" in text
    assert len(text) > 0


def test_list_operations():
    """Test basic list operations"""
    items = ["RSS", "Snowflake", "AI", "App"]
    assert len(items) == 4
    assert "Snowflake" in items
    items.append("Test")
    assert len(items) == 5
