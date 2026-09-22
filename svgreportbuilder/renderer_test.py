from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from svgreportbuilder import (
    FixedSlots,
    ImageField,
    ImageSource,
    SvgDataError,
    SvgReportTemplate,
    SvgSpecError,
    TextField,
)

SVG_NS = "http://www.w3.org/2000/svg"
XHTML_NS = "http://www.w3.org/1999/xhtml"


def _svg(*ids: str) -> str:
    rects = "".join(
        f'<rect id="{element_id}" x="0" y="0" width="10" height="2"/>'
        for element_id in ids
    )
    return f'<svg xmlns="{SVG_NS}">{rects}</svg>'


def _divs(output: str) -> list[ET.Element]:
    root = ET.fromstring(output)
    return root.findall(f".//{{{XHTML_NS}}}div")


def _element(root: ET.Element, path: str) -> ET.Element:
    element = root.find(path)
    assert element is not None
    return element


def _foreign_object(root: ET.Element, target_id: str) -> ET.Element:
    target = _element(root, f".//*[@id='{target_id}']")
    parent = next(parent for parent in root.iter() if target in list(parent))
    return list(parent)[list(parent).index(target) + 1]


def test_report_template_uses_fixed_slots_and_data_paint_paths() -> None:
    report = SvgReportTemplate(
        svg=_svg("item_0_name", "item_1_name"),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=2,
                index="row",
                fields=[
                    TextField(
                        value_path="name",
                        target_id="item_{row}_name",
                        target_fill_path="appearance.fill",
                    )
                ],
            )
        ],
    )

    output = report.render(
        {
            "items": [{"name": "A", "appearance": {"fill": "#abc"}}],
        }
    )
    root = ET.fromstring(output)
    assert _element(root, ".//*[@id='item_0_name']").get("style") == "fill:#abc;"
    assert _element(root, ".//*[@id='item_1_name']").get("style") is None
    divs = _divs(output)
    assert [div.text for div in divs] == ["A", None]
    assert (
        root.findall(f".//{{{SVG_NS}}}foreignObject")[1].get("data-svgrb-value-path")
        == "items.1.name"
    )


def test_field_factory_can_change_one_field_by_slot_index() -> None:
    report = SvgReportTemplate(
        svg=_svg("item_0", "item_1"),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=2,
                index="row",
                fields=[
                    lambda row: TextField(
                        value_path="name",
                        target_id=f"item_{row}",
                        foreign_object_style={
                            "overflow": "visible" if row == 0 else "hidden"
                        },
                    )
                ],
            )
        ],
    )
    output = report.render({"items": [{"name": "A"}, {"name": "B"}]})
    objects = ET.fromstring(output).findall(f".//{{{SVG_NS}}}foreignObject")
    assert objects[0].get("style") == "overflow:visible;"
    assert objects[1].get("style") == "overflow:hidden;"


def test_nested_fixed_slots_use_outer_and_inner_indices() -> None:
    report = SvgReportTemplate(
        svg=_svg("group_0_item_0", "group_0_item_1"),
        fields=[
            FixedSlots(
                value_path="groups",
                capacity=1,
                index="group",
                fields=[
                    FixedSlots(
                        value_path="items",
                        capacity=2,
                        index="row",
                        fields=[
                            TextField(
                                value_path="name",
                                target_id="group_{group}_item_{row}",
                            )
                        ],
                    )
                ],
            )
        ],
    )
    output = report.render({"groups": [{"items": [{"name": "A"}]}]})
    assert [div.text for div in _divs(output)] == ["A", None]


def test_empty_slot_does_not_use_default_or_read_paint_path() -> None:
    report = SvgReportTemplate(
        svg=_svg("item_0", "item_1"),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=2,
                index="row",
                fields=[
                    TextField(
                        value_path="name",
                        target_id="item_{row}",
                        default="fallback",
                        target_fill_path="$.appearance.fill",
                    )
                ],
            )
        ],
    )
    output = report.render({"appearance": {"fill": "red"}, "items": [{"name": "A"}]})
    assert [div.text for div in _divs(output)] == ["A", None]


def test_image_field_and_absolute_root_path_work_inside_slots() -> None:
    report = SvgReportTemplate(
        svg=_svg("item_0"),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=1,
                index="row",
                fields=[
                    ImageField(
                        value_path="image",
                        target_id="item_{row}",
                        target_fill_path="$.appearance.fill",
                    )
                ],
            )
        ],
    )
    output = report.render(
        {
            "appearance": {"fill": "none"},
            "items": [{"image": ImageSource(data=b"x", mime_type="image/png")}],
        }
    )
    root = ET.fromstring(output)
    assert _element(root, ".//*[@id='item_0']").get("style") == "fill:none;"
    image = root.find(f".//{{{XHTML_NS}}}img")
    assert image is not None
    assert image.get("src") == "data:image/png;base64,eA=="


def test_numeric_mapping_components_remain_string_keys() -> None:
    report = SvgReportTemplate(
        svg=_svg("box"),
        fields=[TextField(value_path="values.0", target_id="box")],
    )
    output = report.render({"values": {"0": "mapped"}})
    assert _divs(output)[0].text == "mapped"


def test_invalid_new_definitions_fail_during_construction() -> None:
    with pytest.raises(SvgSpecError):
        SvgReportTemplate(
            svg=_svg("a"),
            fields=[
                FixedSlots(
                    value_path="items",
                    capacity=1,
                    index="row",
                    fields=[
                        TextField(value_path="name", target_id="missing_{unknown}")
                    ],
                )
            ],
        )

    with pytest.raises(SvgDataError):
        SvgReportTemplate(
            svg=_svg("a"),
            fields=[TextField(value_path="value", target_id="a")],
        ).render({})


def test_text_values_defaults_and_xml_characters_are_handled_generically() -> None:
    report = SvgReportTemplate(
        svg=_svg("name", "amount", "optional"),
        fields=[
            TextField(value_path="customer.name", target_id="name"),
            TextField(value_path="values.0", target_id="amount"),
            TextField(value_path="missing", target_id="optional", default="fallback"),
        ],
    )

    output = report.render({"customer": {"name": "A & <B>"}, "values": {"0": 132000}})
    assert [div.text for div in _divs(output)] == ["A & <B>", "132000", "fallback"]
    assert "A &amp; &lt;B&gt;" in output


def test_render_applies_field_styles_and_preserves_the_original_template() -> None:
    svg = (
        f'<svg xmlns="{SVG_NS}">'
        '<rect id="label" x="0" y="0" width="10" height="2" style="stroke:#000;"/>'
        '<rect id="image" x="0" y="3" width="10" height="2" style="fill:#fff;"/>'
        "</svg>"
    )
    report = SvgReportTemplate(
        svg=svg,
        fields=[
            TextField(
                value_path="label",
                target_id="label",
                container_style={"padding": "2px"},
                foreign_object_style={"overflow": "visible"},
                hide_target=True,
                target_fill_path="appearance.fill",
                target_stroke_path="appearance.stroke",
            ),
            ImageField(
                value_path="image",
                target_id="image",
                container_style={"padding": "3px"},
                image_style={"object-fit": "contain"},
                remove_stroke=True,
            ),
        ],
    )
    image = ImageSource(data=b"x", mime_type="image/png")

    first = report.render(
        {
            "label": "first",
            "appearance": {"fill": "red", "stroke": "blue"},
            "image": image,
        }
    )
    second = report.render(
        {
            "label": "second",
            "appearance": {"fill": "green", "stroke": "purple"},
            "image": image,
        }
    )

    first_root = ET.fromstring(first)
    second_root = ET.fromstring(second)
    first_label = _element(first_root, ".//*[@id='label']")
    assert first_label.get("style") == "stroke:#000;fill:red;stroke:blue;"
    assert first_label.get("visibility") == "hidden"
    assert _foreign_object(first_root, "label").get("style") == "overflow:visible;"
    assert "padding:2px" in (_divs(first)[0].get("style") or "")

    first_image = _element(first_root, ".//*[@id='image']")
    assert first_image.get("style") == "fill:#fff;stroke:none;"
    image_element = _foreign_object(first_root, "image").find(f".//{{{XHTML_NS}}}img")
    assert image_element is not None
    assert image_element.get("src") == "data:image/png;base64,eA=="
    assert "object-fit:contain" in (image_element.get("style") or "")

    assert _element(second_root, ".//*[@id='label']").get("style") == (
        "stroke:#000;fill:green;stroke:purple;"
    )
    assert "fill:red" not in second


@pytest.mark.parametrize("white_space", ["pre", "pre-wrap", "break-spaces"])
def test_image_container_has_no_generated_whitespace(white_space: str) -> None:
    report = SvgReportTemplate(
        svg=_svg("image"),
        fields=[
            ImageField(
                target_id="image",
                value_path="image",
                container_style={"white-space": white_space},
            )
        ],
    )
    source = ImageSource(
        data=(
            f'<svg xmlns="{SVG_NS}" width="1" height="1">'
            '<rect width="1" height="1"/></svg>'
        ).encode("utf-8"),
        mime_type="image/svg+xml",
    )

    container = _divs(report.render({"image": source}))[0]
    image = _element(container, f"{{{XHTML_NS}}}img")

    # Pretty-printing whitespace becomes visible content with these CSS values.
    assert container.text is None
    assert image.tail is None


def test_optional_images_and_invalid_values_are_checked_by_the_library() -> None:
    image = ImageSource(data=b"x", mime_type="image/png")
    optional = SvgReportTemplate(
        svg=_svg("image"),
        fields=[ImageField(value_path="image", target_id="image", default=image)],
    )
    default_root = ET.fromstring(optional.render({}))
    none_root = ET.fromstring(optional.render({"image": None}))
    assert (
        _foreign_object(default_root, "image").find(f".//{{{XHTML_NS}}}img") is not None
    )
    assert _foreign_object(none_root, "image").find(f".//{{{XHTML_NS}}}img") is None

    text = SvgReportTemplate(
        svg=_svg("text"), fields=[TextField(value_path="value", target_id="text")]
    )
    with pytest.raises(SvgDataError, match="must resolve to a text value"):
        text.render({"value": {"not": "text"}})

    image_report = SvgReportTemplate(
        svg=_svg("image"), fields=[ImageField(value_path="value", target_id="image")]
    )
    with pytest.raises(SvgDataError, match="must resolve to None or an ImageSource"):
        image_report.render({"value": "not-an-image"})


def test_fixed_slots_enforce_item_bounds_before_rendering() -> None:
    report = SvgReportTemplate(
        svg=_svg("item_0"),
        fields=[
            FixedSlots(
                value_path="items",
                capacity=1,
                min_items=1,
                index="row",
                fields=[TextField(value_path="name", target_id="item_{row}")],
            )
        ],
    )
    with pytest.raises(SvgDataError, match="expected between 1 and 1"):
        report.render({"items": []})
    with pytest.raises(SvgDataError, match="expected between 1 and 1"):
        report.render({"items": [{"name": "A"}, {"name": "B"}]})
