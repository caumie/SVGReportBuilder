from __future__ import annotations

import pytest

from svgreportbuilder import SvgSpecError
from svgreportbuilder.css import merged_style, style_text, validate_paint, validate_style


def test_simple_declarations_are_serialized_in_input_order() -> None:
    style = {"font-size": "12px", "color": "red"}
    validate_style(style, "field")

    assert style_text(style) == "font-size:12px;color:red;"
    assert merged_style({"width": "100%", "color": "black"}, {"color": "red"}) == (
        "width:100%;color:red;"
    )


@pytest.mark.parametrize(
    "style",
    [
        {"font size": "12px"},
        {"font-size": "12px; color:red"},
        {"font-size": "bad\x00value"},
        {"color": "red/*"},
        {"color": "red*/blue"},
    ],
)
def test_css_outside_the_reduced_input_spec_is_rejected(style: dict[str, str]) -> None:
    with pytest.raises(SvgSpecError):
        validate_style(style, "field")


@pytest.mark.parametrize(
    "value",
    [
        "#abc",
        "#abcd",
        "#aabbcc",
        "#aabbccdd",
        "none",
        "currentColor",
        "context-fill",
        "transparent",
        "rebeccapurple",
        "rgb(255, 0, 16)",
        "rgba(255, 0, 16, .5)",
        "rgb(100% 0% 50% / 25%)",
        "hsl(120, 50%, 40%)",
        "hsla(120deg 50% 40% / .5)",
    ],
)
def test_data_paint_accepts_literal_colors(value: str) -> None:
    validate_paint(value, "target")


@pytest.mark.parametrize(
    "value",
    [
        "url(https://example.com/a.svg)",
        "url(#local-gradient)",
        'image-set("https://example.com/a.png")',
        "rgb(1 2 3 / var(--alpha))",
        "red/*",
        "red*/",
        "#12345",
        "red;stroke:blue",
        "rgb(1, 2, 3) url(#x)",
    ],
)
def test_data_paint_rejects_references_and_invalid_literals(value: str) -> None:
    with pytest.raises(SvgSpecError):
        validate_paint(value, "target")
