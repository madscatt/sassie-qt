"""Pure GenApp-style form state evaluation for the Qt prototype."""

from __future__ import annotations

from dataclasses import dataclass

from sassie_qt.menu_loader import ModuleField
from sassie_qt.value_helpers import field_value_to_text, split_repeated, truthy


@dataclass(frozen=True)
class FieldState:
    """Computed UI state for one GenApp field."""

    visible: bool
    repeat_count: int = 1
    integer_pair_dimensions: tuple[int, int] | None = None
    integer_pair_headers: tuple[list[str], list[str]] = ((), ())
    ordinary_integer_repeater: bool = False
    integer_pair_repeater: bool = False


@dataclass(frozen=True)
class FormState:
    """Computed state for a whole module form."""

    fields: dict[str, FieldState]
    values: dict[str, str]


class FormStateEngine:
    """Evaluate GenApp dependency/repeater metadata without Qt widgets."""

    def __init__(self, fields: tuple[ModuleField, ...]) -> None:
        self.fields = fields
        self.field_by_id = {field.id: field for field in fields}

    def evaluate(self, values: dict[str, str]) -> FormState:
        resolved_values = self._defaulted_values(values)
        resolved_values = self._sync_integer_fields(resolved_values)
        field_states = {
            field.id: self._field_state(field, resolved_values)
            for field in self.fields
        }
        return FormState(fields=field_states, values=resolved_values)

    def is_integer_repeated_field(self, field: ModuleField) -> bool:
        if not field.repeat or ":" in field.repeat:
            return False
        controller = self.field_by_id.get(field.repeat)
        if controller is None or controller.field_type != "integer":
            return False
        if not controller.repeat or ":" in controller.repeat:
            return True
        parent_controller = self.field_by_id.get(controller.repeat)
        return parent_controller is None or parent_controller.field_type != "integer"

    def is_integer_pair_repeated_field(self, field: ModuleField) -> bool:
        if not field.repeat or ":" in field.repeat:
            return False
        controller = self.field_by_id.get(field.repeat)
        return controller is not None and controller.field_type == "integerpair"

    def integer_pair_headers(
        self,
        field_id: str,
        values: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        field = self.field_by_id.get(field_id)
        headers = field.headers if field is not None else None
        if not headers:
            return ([], [])

        resolved_values = self._defaulted_values(values)
        row_labels = self._header_labels(headers.get("row", []), resolved_values)
        column_labels = self._header_labels(headers.get("column", []), resolved_values)
        return (row_labels, column_labels)

    def integer_pair_dimensions(
        self,
        field_id: str,
        values: dict[str, str],
    ) -> tuple[int, int]:
        field = self.field_by_id.get(field_id)
        if field is None or not field.calc:
            return (1, 1)

        controller_ids = [
            item.strip()
            for item in field.calc.split(",")
            if item.strip()
        ]
        if len(controller_ids) != 2:
            return (1, 1)

        resolved_values = self._defaulted_values(values)
        return (
            self._integer_value(controller_ids[0], resolved_values, default=1),
            self._integer_value(controller_ids[1], resolved_values, default=1),
        )

    def _field_state(
        self,
        field: ModuleField,
        values: dict[str, str],
    ) -> FieldState:
        ordinary_repeater = self.is_integer_repeated_field(field)
        integer_pair_repeater = self.is_integer_pair_repeated_field(field)
        repeat_count = (
            self._integer_value(field.repeat, values, default=1)
            if ordinary_repeater
            else 1
        )
        integer_pair_dimensions = (
            self.integer_pair_dimensions(field.repeat, values)
            if integer_pair_repeater
            else None
        )
        integer_pair_headers = (
            self.integer_pair_headers(field.repeat, values)
            if integer_pair_repeater
            else ([], [])
        )
        return FieldState(
            visible=self._field_visible(field.id, values, seen=set()),
            repeat_count=repeat_count,
            integer_pair_dimensions=integer_pair_dimensions,
            integer_pair_headers=integer_pair_headers,
            ordinary_integer_repeater=ordinary_repeater,
            integer_pair_repeater=integer_pair_repeater,
        )

    def _sync_integer_fields(self, values: dict[str, str]) -> dict[str, str]:
        sync_sources: dict[str, str] = {}
        for field in self.fields:
            if field.sync and not field.hidden:
                sync_sources.setdefault(field.sync, values.get(field.id, ""))

        synced_values = dict(values)
        for field in self.fields:
            if field.hidden and field.sync in sync_sources:
                synced_values[field.id] = sync_sources[field.sync]
        return synced_values

    def _field_visible(
        self,
        field_id: str,
        values: dict[str, str],
        seen: set[str],
    ) -> bool:
        field = self.field_by_id.get(field_id)
        if field is None:
            return False
        if field.hidden:
            return False
        if field.repeat:
            return self._repeat_condition_is_met(field.repeat, values, seen)
        return True

    def _repeat_condition_is_met(
        self,
        repeat: str,
        values: dict[str, str],
        seen: set[str],
    ) -> bool:
        controller_id, _separator, expected_value = repeat.partition(":")
        controller = self.field_by_id.get(controller_id)
        if controller is None or not self._control_is_active(controller_id, values, seen):
            return False

        controller_value = values.get(controller_id, "")
        if expected_value:
            return controller_value == expected_value
        if controller.hidden and controller.field_type == "integerpair":
            return True
        if controller.field_type == "checkbox":
            return truthy(controller_value)
        if controller.field_type == "integer":
            return self._integer_value(controller_id, values, default=0) > 0
        return bool(controller_value.strip())

    def _control_is_active(
        self,
        field_id: str,
        values: dict[str, str],
        seen: set[str],
    ) -> bool:
        if field_id in seen:
            return True
        field = self.field_by_id.get(field_id)
        if field is None:
            return False
        seen = set(seen)
        seen.add(field_id)
        if field.hidden and field.repeat:
            return self._repeat_condition_is_met(field.repeat, values, seen)
        if field.hidden:
            return True
        if field.repeat:
            return self._repeat_condition_is_met(field.repeat, values, seen)
        return True

    def _integer_value(
        self,
        field_id: str,
        values: dict[str, str],
        default: int,
    ) -> int:
        try:
            value = int(values.get(field_id, ""))
        except ValueError:
            return default
        field = self.field_by_id.get(field_id)
        minimum = 0 if field is None or field.minimum is None else field.minimum
        return max(minimum, value)

    def _header_labels(
        self,
        source_field_ids,
        values: dict[str, str],
    ) -> list[str]:
        labels: list[str] = []
        for source_field_id in source_field_ids:
            labels.extend(split_repeated(values.get(str(source_field_id), "")))
        return labels

    def _defaulted_values(self, values: dict[str, str]) -> dict[str, str]:
        defaulted = {
            field.id: field_value_to_text(field.default)
            for field in self.fields
        }
        defaulted.update(values)
        return defaulted
