"""Public error contracts for invalid templates, definitions, and input data."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import cast

import pytest

from svgreportbuilder import (
    Data,
    FieldDefinition,
    FieldSpec,
    FixedSlots,
    ImageField,
    ImageSource,
    SvgDataError,
    SvgReportTemplate,
    SvgSpecError,
    SvgTemplateError,
    TextField,
)

SVG_NS = "http://www.w3.org/2000/svg"
RECT = '<rect id="box" x="0" y="0" width="10" height="2"/>'
_INVALID_EMPTY_SLOT_DATA: list[tuple[Data, str]] = [
    ({}, "was not found"),
    ({"items": []}, "expected between 1 and 1"),
    ({"items": [{}, {}]}, "expected between 1 and 1"),
    ({"items": [123]}, "must contain mappings"),
]


def _svg(body: str = "") -> str:
    return f'<svg xmlns="{SVG_NS}">{body}</svg>'


@pytest.mark.parametrize(
    ("svg", "reason"),
    [
        ("<svg", "not well-formed"),
        (f'<html xmlns="{SVG_NS}"/>', "root"),
        (_svg(RECT + RECT), "duplicate SVG id"),
        (_svg(), "was not found"),
        (_svg('<circle id="box"/>'), "must identify a rect"),
        (_svg('<rect id="box" x="0" y="0" height="2"/>'), "missing width"),
        (
            _svg('<rect id="box" x="0" y="0" width="10%" height="2"/>'),
            "invalid width",
        ),
        (_svg(f"<defs>{RECT}</defs>"), "non-rendered"),
        (_svg(f"<metadata>{RECT}</metadata>"), "non-rendered"),
        (_svg(f"<defs><svg>{RECT}</svg></defs>"), "non-rendered"),
        (_svg(f"<switch>{RECT}</switch>"), "non-rendered"),
        (
            _svg(
                '<rect id="box" x="0" y="0" width="10" height="2" '
                'transform="translate(1)"/>'
            ),
            "must not have transform",
        ),
    ],
)
def test_invalid_svg_structure_raises_template_error(svg: str, reason: str) -> None:
    with pytest.raises(SvgTemplateError, match=reason):
        SvgReportTemplate(
            svg=svg,
            fields=[TextField(value_path="value", target_id="box")],
        )


@pytest.mark.parametrize(
    ("data", "reason"),
    _INVALID_EMPTY_SLOT_DATA,
)
def test_empty_slot_fields_still_validate_the_array(data: Data, reason: str) -> None:
    report = SvgReportTemplate(
        svg=_svg(),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=1,
                min_items=1,
                index="row",
                fields=[],
            )
        ],
    )

    with pytest.raises(SvgDataError, match=reason):
        report.render(data)


def test_nested_empty_slot_fields_check_only_present_parents() -> None:
    report = SvgReportTemplate(
        svg=_svg(),
        fields=[
            FixedSlots(
                value_path="groups",
                capacity=2,
                index="group",
                fields=[
                    FixedSlots(
                        value_path="items",
                        capacity=1,
                        min_items=1,
                        index="row",
                        fields=[],
                    )
                ],
            )
        ],
    )

    assert ET.fromstring(report.render({"groups": []})).tag == f"{{{SVG_NS}}}svg"
    assert ET.fromstring(report.render({"groups": [{"items": [{}]}]})).tag == (
        f"{{{SVG_NS}}}svg"
    )
    with pytest.raises(SvgDataError, match="groups.0.items"):
        report.render({"groups": [{}]})


@pytest.mark.parametrize(
    ("name", "bad_value"),
    [
        ("capacity", None),
        ("capacity", "1"),
        ("capacity", 1.5),
        ("capacity", True),
        ("capacity", 0),
        ("min_items", None),
        ("min_items", "0"),
        ("min_items", 0.5),
        ("min_items", True),
        ("min_items", -1),
        ("min_items", 2),
    ],
)
def test_invalid_slot_bounds_raise_spec_error(name: str, bad_value: object) -> None:
    with pytest.raises(SvgSpecError, match=name):
        if name == "capacity":
            slots = FixedSlots(
                value_path="items",
                capacity=cast(int, bad_value),
                index="row",
                fields=[],
            )
        else:
            slots = FixedSlots(
                value_path="items",
                capacity=1,
                min_items=cast(int, bad_value),
                index="row",
                fields=[],
            )
        SvgReportTemplate(svg=_svg(), fields=[slots])


@pytest.mark.parametrize("bad_child", [None, 123, "field", object()])
def test_invalid_slot_child_raises_spec_error(bad_child: object) -> None:
    with pytest.raises(SvgSpecError):
        slots = FixedSlots(
            value_path="items",
            capacity=1,
            index="row",
            fields=[cast(FieldSpec, bad_child)],
        )
        SvgReportTemplate(svg=_svg(), fields=[slots])


def test_factory_returning_an_invalid_child_raises_spec_error() -> None:
    def invalid_factory(_index: int) -> FieldSpec:
        return cast(FieldSpec, object())

    with pytest.raises(SvgSpecError):
        slots = FixedSlots(
            value_path="items",
            capacity=1,
            index="row",
            fields=[invalid_factory],
        )
        SvgReportTemplate(svg=_svg(), fields=[slots])


def test_invalid_top_level_field_raises_spec_error() -> None:
    with pytest.raises(SvgSpecError):
        SvgReportTemplate(
            svg=_svg(),
            fields=[cast(FieldDefinition, object())],
        )


@pytest.mark.parametrize("name", ["index", "value_path"])
def test_non_string_slot_definition_raises_spec_error(name: str) -> None:
    with pytest.raises(SvgSpecError):
        if name == "index":
            slots = FixedSlots(
                value_path="items",
                capacity=1,
                index=cast(str, 123),
                fields=[],
            )
        else:
            slots = FixedSlots(
                value_path=cast(str, None),
                capacity=1,
                index="row",
                fields=[],
            )
        SvgReportTemplate(svg=_svg(), fields=[slots])


@pytest.mark.parametrize("name", ["target_id", "value_path"])
def test_non_string_text_field_definition_raises_spec_error(name: str) -> None:
    with pytest.raises(SvgSpecError):
        if name == "target_id":
            text_field = TextField(target_id=cast(str, 123), value_path="value")
        else:
            text_field = TextField(target_id="box", value_path=cast(str, None))
        SvgReportTemplate(svg=_svg(RECT), fields=[text_field])


@pytest.mark.parametrize(
    "bad_mime", [None, 123, "image/png; charset=utf-8", "image/", "text/html"]
)
def test_invalid_image_mime_raises_data_error(bad_mime: object) -> None:
    report = SvgReportTemplate(
        svg=_svg(RECT),
        fields=[ImageField(value_path="image", target_id="box")],
    )

    with pytest.raises(SvgDataError):
        report.render(
            {"image": ImageSource(data=b"image", mime_type=cast(str, bad_mime))}
        )


def test_image_mime_is_case_insensitive() -> None:
    report = SvgReportTemplate(
        svg=_svg(RECT),
        fields=[ImageField(value_path="image", target_id="box")],
    )

    assert "data:IMAGE/PNG;base64," in report.render(
        {"image": ImageSource(data=b"image", mime_type="IMAGE/PNG")}
    )


def test_non_byte_image_data_raises_data_error() -> None:
    report = SvgReportTemplate(
        svg=_svg(RECT),
        fields=[ImageField(value_path="image", target_id="box")],
    )

    with pytest.raises(SvgDataError):
        report.render(
            {"image": ImageSource(data=cast(bytes, "image"), mime_type="image/png")}
        )


def test_external_paint_reference_raises_data_error() -> None:
    report = SvgReportTemplate(
        svg=_svg(RECT),
        fields=[
            TextField(
                value_path="value",
                target_id="box",
                target_fill_path="fill",
            )
        ],
    )

    with pytest.raises(SvgDataError, match="fill value"):
        report.render({"value": "text", "fill": "url(https://example.com/p.svg)"})


@pytest.mark.parametrize("bad_fields", [None, {}, "field", b"field"])
def test_non_sequence_slot_children_raise_spec_error(bad_fields: object) -> None:
    with pytest.raises(SvgSpecError, match="FixedSlots.fields"):
        FixedSlots(
            value_path="items",
            capacity=1,
            index="row",
            fields=cast(list[FieldSpec], bad_fields),
        )


@pytest.mark.parametrize("bad_fields", [None, {}, "field", b"field"])
def test_non_sequence_report_fields_raise_spec_error(bad_fields: object) -> None:
    with pytest.raises(SvgSpecError, match="SvgReportTemplate.fields"):
        SvgReportTemplate(svg=_svg(), fields=cast(list[FieldDefinition], bad_fields))


def test_non_string_svg_raises_template_error() -> None:
    with pytest.raises(SvgTemplateError, match="svg must be a string"):
        SvgReportTemplate(svg=cast(str, None), fields=[])


def test_non_mapping_render_data_raises_data_error_even_with_default() -> None:
    report = SvgReportTemplate(
        svg=_svg(RECT),
        fields=[TextField(target_id="box", value_path="value", default="fallback")],
    )

    with pytest.raises(SvgDataError, match="data must be a mapping"):
        report.render(cast(Data, None))


def test_non_mapping_field_style_raises_spec_error() -> None:
    with pytest.raises(SvgSpecError, match="style must be a mapping"):
        TextField(
            target_id="box",
            value_path="value",
            container_style=cast(dict[str, str], None),
        )


def test_non_bool_field_flag_raises_spec_error() -> None:
    with pytest.raises(SvgSpecError, match="hide_target"):
        SvgReportTemplate(
            svg=_svg(RECT),
            fields=[
                TextField(
                    target_id="box",
                    value_path="value",
                    hide_target=cast(bool, "yes"),
                )
            ],
        )


def test_external_style_reference_raises_spec_error() -> None:
    with pytest.raises(SvgSpecError, match="CSS function"):
        SvgReportTemplate(
            svg=_svg(RECT),
            fields=[
                TextField(
                    target_id="box",
                    value_path="value",
                    container_style={
                        "background-image": "url(https://example.com/a.png)"
                    },
                )
            ],
        )
