from __future__ import annotations

import inspect
from collections.abc import MutableMapping
from typing import cast

import pytest

from svgreportbuilder.models import (
    UNSET,
    FixedSlots,
    ImageField,
    ImageSource,
    SvgReportTemplate,
    SvgSpecError,
    TextField,
)


def test_public_definitions_are_keyword_only() -> None:
    definitions = (TextField, ImageField, ImageSource, FixedSlots, SvgReportTemplate)
    for definition in definitions:
        parameters = inspect.signature(definition).parameters.values()
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters
        )


def test_field_styles_are_immutable_snapshots() -> None:
    style = {"color": "red"}
    text = TextField(target_id="text", value_path="value", container_style=style)
    image = ImageField(target_id="image", value_path="value", image_style=style)
    style["color"] = "blue"

    assert text.container_style == {"color": "red"}
    assert image.image_style == {"color": "red"}
    with pytest.raises(TypeError):
        cast(MutableMapping[str, str], text.container_style)["color"] = "blue"


def test_definition_sequences_are_materialized() -> None:
    field = TextField(target_id="value", value_path="value")
    slots = FixedSlots(value_path="items", capacity=1, index="row", fields=[field])
    template = SvgReportTemplate(
        svg=(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect id="value" x="0" y="0" width="1" height="1"/>'
            "</svg>"
        ),
        fields=[field],
    )

    assert slots.fields == (field,)
    assert template.fields == (field,)


def test_invalid_definition_sequences_are_rejected() -> None:
    with pytest.raises(SvgSpecError, match="FixedSlots.fields must be a sequence"):
        FixedSlots(value_path="items", capacity=1, index="row", fields=object())  # type: ignore[arg-type]

    with pytest.raises(
        SvgSpecError, match="SvgReportTemplate.fields must be a sequence"
    ):
        SvgReportTemplate(svg="<svg xmlns='http://www.w3.org/2000/svg'/>", fields=object())  # type: ignore[arg-type]


def test_unset_has_a_stable_display_value() -> None:
    assert str(UNSET) == "UNSET"
    assert repr(UNSET) == "UNSET"
