from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pytest

from svgreportbuilder import SvgSpecError
from svgreportbuilder.css import merged_style, style_text, validate_paint, validate_style


def test_simple_declarations_are_serialized_in_input_order() -> None:
    style = {"font-size": "12px", "color": "rgb(30, 40, 50)"}
    validate_style(style, "field")

    assert style_text(style) == "font-size:12px;color:rgb(30, 40, 50);"
    assert merged_style({"width": "100%", "color": "black"}, {"color": "red"}) == (
        "width:100%;color:red;"
    )


def test_safe_css_functions_and_quoted_parentheses_are_accepted() -> None:
    validate_style(
        {
            "width": "calc(100% - 2px)",
            "background": "linear-gradient(rgb(0, 0, 0), #fff)",
            "transform": "translate(4px, 2px)",
            "font-family": '"Noto (CJK)", sans-serif',
        },
        "field",
    )


@pytest.mark.parametrize(
    "style",
    [
        {"font size": "12px"},
        {"font-size": "12px; color:red"},
        {"font-size": "bad\x00value"},
        {"color": "red/*"},
        {"color": "red*/blue"},
        {"font-family": '"unclosed'},
        {"width": "calc(100% - 2px"},
        {"width": "100%)"},
    ],
)
def test_css_outside_the_reduced_input_spec_is_rejected(style: dict[str, str]) -> None:
    with pytest.raises(SvgSpecError):
        validate_style(style, "field")


@pytest.mark.parametrize("style", [{1: "red"}, {"color": 12}])
def test_css_runtime_types_raise_spec_error(style: object) -> None:
    with pytest.raises(SvgSpecError):
        validate_style(cast(Mapping[str, str], style), "field")


@pytest.mark.parametrize(
    "value",
    [
        "url(https://example.com/a.svg)",
        "URL(#local)",
        "url (https://example.com/a.svg)",
        "u\\72l(https://example.com/a.svg)",
        'image-set("https://example.com/a.png" 1x)',
        '-webkit-image-set("https://example.com/a.png" 1x)',
        "var(--remote-image)",
        "attr(data-image url)",
        "paint(remote-image)",
        "calc(100% - var(--size))",
        "red\n@import 'https://example.com/a.css'",
    ],
)
def test_css_reference_functions_and_escape_bypasses_are_rejected(value: str) -> None:
    with pytest.raises(SvgSpecError):
        validate_style({"background-image": value}, "field")


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
        "rgb(1 2 3" + " " * 300 + "x)",
    ],
)
def test_data_paint_rejects_references_and_invalid_literals(value: str) -> None:
    with pytest.raises(SvgSpecError):
        validate_paint(value, "target")
