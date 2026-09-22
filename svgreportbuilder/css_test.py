from __future__ import annotations

import pytest

from svgreportbuilder import SvgSpecError
from svgreportbuilder.css import merged_style, style_text, validate_style


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
    ],
)
def test_css_outside_the_reduced_input_spec_is_rejected(style: dict[str, str]) -> None:
    with pytest.raises(SvgSpecError):
        validate_style(style, "field")
