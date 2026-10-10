import pytest

from shoppy.parsing import (
    command_pattern,
    get_command_args,
    ids_except,
    parse_numbers,
    resolve_numbers,
    split_items,
)


@pytest.mark.parametrize(
    "text",
    ["/add milk", "@shoppy_bot /add milk", "/add@shoppy_bot milk", "/add", "  /add milk"],
)
def test_command_pattern_matches(text):
    assert command_pattern("add").search(text)


@pytest.mark.parametrize(
    "text",
    ["buy milk /add", "/address", "/clearexcept 1", "please /add milk", "/added"],
)
def test_command_pattern_rejects(text):
    assert not command_pattern("add").search(text)


def test_clear_pattern_does_not_match_clearexcept_prefix():
    assert not command_pattern("clear").search("/clearexcept 1")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("/add milk, bread", "milk, bread"),
        ("@shoppy_bot /add milk", "milk"),
        ("/add@shoppy_bot  milk ", "milk"),
        ("/add", ""),
        ("/add\nmilk", "milk"),
        ("/done 1", None),
    ],
)
def test_get_command_args(text, expected):
    assert get_command_args(text, "add") == expected


def test_split_items_drops_empty_entries():
    assert split_items(" milk ,, bread, ") == ["milk", "bread"]


def test_parse_numbers():
    assert parse_numbers("1, 2 5,2") == {1, 2, 5}
    assert parse_numbers("none") == set()


ITEMS = [(10, "milk"), (11, "bread"), (12, "eggs")]


def test_resolve_numbers():
    assert resolve_numbers(ITEMS, {1, 3, 0, 7}) == ([10, 12], [0, 7])


def test_ids_except():
    assert ids_except(ITEMS, {2}) == [10, 12]
    assert ids_except(ITEMS, {9}) == [10, 11, 12]
