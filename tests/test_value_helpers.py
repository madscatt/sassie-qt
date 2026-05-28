from sassie_qt.value_helpers import (
    bool_text,
    field_value_to_text,
    listbox_bool,
    nested_values,
    split_repeated,
    truthy,
)


def test_truthy_accepts_qt_and_form_boolean_text() -> None:
    assert truthy("true")
    assert truthy("1")
    assert truthy("yes")
    assert truthy("on")
    assert not truthy("false")
    assert not truthy("")


def test_bool_text_uses_sassie_boolean_text() -> None:
    assert bool_text("true") == "True"
    assert bool_text("false") == "False"


def test_listbox_bool_maps_selected_code() -> None:
    assert listbox_bool("c2", true_code="c2") == "True"
    assert listbox_bool("c1", true_code="c2") == "False"


def test_split_repeated_trims_empty_cells() -> None:
    assert split_repeated(" a, b ,, c ") == ["a", "b", "c"]


def test_nested_values_splits_rows_and_cells() -> None:
    assert nested_values("a,b; c,d") == [["a", "b"], ["c", "d"]]


def test_field_value_to_text_preserves_configurable_list_separator() -> None:
    assert field_value_to_text(["a", "b"]) == "a,b"
    assert field_value_to_text(["a", "b"], list_separator=", ") == "a, b"
