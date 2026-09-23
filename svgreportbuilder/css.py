"""レンダラーが生成する単純なinline CSSの扱い。"""

from __future__ import annotations

import re
import string
from collections.abc import Mapping
from typing import cast

from .models import SvgSpecError

# 機能の塊: CSSは完全解釈せず、1値1宣言だけを許可する。
# 宣言を分断するセミコロンとコメント区切りを値に許可しない。
_PROPERTY_RE = re.compile(
    r"^(?:--[A-Za-z0-9_-]+|-[A-Za-z_][A-Za-z0-9_-]*|[A-Za-z_][A-Za-z0-9_-]*)$"
)
_CSS_NAME_CHARS = frozenset(string.ascii_letters + string.digits + "_-")
# 任意の関数を通すとurl()やimage-set()からリソースを読めるため、
# 外部参照を持たない関数だけを列挙する。関数内の関数も同じ規則で検査する。
_ALLOWED_STYLE_FUNCTIONS = frozenset(
    {
        "rgb", "rgba", "hsl", "hsla", "hwb", "lab", "lch", "oklab", "oklch",
        "color", "color-mix", "calc", "min", "max", "clamp",
        "linear-gradient", "repeating-linear-gradient",
        "radial-gradient", "repeating-radial-gradient",
        "conic-gradient", "repeating-conic-gradient",
        "matrix", "matrix3d", "translate", "translatex", "translatey",
        "translatez", "translate3d", "rotate", "rotatex", "rotatey",
        "rotatez", "rotate3d", "scale", "scalex", "scaley", "scalez",
        "scale3d", "skew", "skewx", "skewy", "perspective",
        "blur", "brightness", "contrast", "grayscale", "hue-rotate",
        "invert", "opacity", "saturate", "sepia", "drop-shadow",
        "cubic-bezier", "steps",
    }
)

# データ由来のfill/strokeは単色だけを受理する。url()等の参照構文を
# 汎用CSSとして解析する代わりに、許可する文法を限定する。
_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?"
_PERCENTAGE = rf"{_NUMBER}%"
_RGB_COMPONENT = rf"(?:{_NUMBER}|{_PERCENTAGE})"
_HUE = rf"{_NUMBER}(?:deg|grad|rad|turn)?"
_ALPHA = _RGB_COMPONENT
_SPACE = r"[ \t]*"
_REQUIRED_SPACE = r"[ \t]+"


def _function_pattern(first: str, second: str, third: str) -> str:
    comma_values = (
        rf"{first}{_SPACE},{_SPACE}{second}{_SPACE},{_SPACE}{third}"
        rf"(?:{_SPACE},{_SPACE}{_ALPHA})?"
    )
    space_values = (
        rf"{first}{_REQUIRED_SPACE}{second}{_REQUIRED_SPACE}{third}"
        rf"(?:{_SPACE}/{_SPACE}{_ALPHA})?"
    )
    return rf"(?:{comma_values}|{space_values})"


_RGB_FUNCTION = _function_pattern(_RGB_COMPONENT, _RGB_COMPONENT, _RGB_COMPONENT)
_HSL_FUNCTION = _function_pattern(_HUE, _PERCENTAGE, _PERCENTAGE)
_MAX_PAINT_LENGTH = 256
_PAINT_RE = re.compile(
    rf"(?:\#[0-9a-f]{{3}}|\#[0-9a-f]{{4}}|\#[0-9a-f]{{6}}|\#[0-9a-f]{{8}}"
    rf"|[a-z]+|context-(?:fill|stroke)"
    rf"|rgba?\({_SPACE}{_RGB_FUNCTION}{_SPACE}\)"
    rf"|hsla?\({_SPACE}{_HSL_FUNCTION}{_SPACE}\))",
    re.IGNORECASE,
)


def _validate_xml_characters(value: str, context: str) -> None:
    for index, character in enumerate(value):
        codepoint = ord(character)
        allowed = (
            codepoint in (0x9, 0xA, 0xD)
            or 0x20 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        )
        if not allowed:
            raise SvgSpecError(
                f"{context} contains an XML 1.0 forbidden character "
                f"U+{codepoint:04X} at index {index}"
            )


def _validate_css_functions(value: str, name: str) -> None:
    """引用文字列を除く括弧を走査し、許可した関数だけを通す。"""
    quote: str | None = None
    depth = 0
    for index, character in enumerate(value):
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in ('"', "'"):
            quote = character
        elif character == "(":
            start = index
            while start > 0 and value[start - 1] in _CSS_NAME_CHARS:
                start -= 1
            function_name = value[start:index].lower()
            if function_name not in _ALLOWED_STYLE_FUNCTIONS:
                raise SvgSpecError(
                    f"{name} CSS function {function_name!r} is not allowed"
                )
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise SvgSpecError(f"{name} CSS values have an unmatched ')'")
    if quote is not None or depth != 0:
        raise SvgSpecError(f"{name} CSS values have an unclosed quote or function")


def validate_style(style: Mapping[str, str], name: str) -> None:
    """style辞書を検証する。既存SVGのstyle属性は解析しない。"""
    for key, value in style.items():
        if not isinstance(cast(object, key), str):
            raise SvgSpecError(f"{name} CSS property names must be strings")
        if not _PROPERTY_RE.fullmatch(key):
            raise SvgSpecError(f"{name} contains an invalid CSS property {key!r}")
        if not isinstance(cast(object, value), str):
            raise SvgSpecError(f"{name} CSS values must be strings")
        if ";" in value:
            raise SvgSpecError(f"{name} CSS values must not contain ';'")
        if "/*" in value or "*/" in value:
            raise SvgSpecError(f"{name} CSS values must not contain comments")
        if "@" in value:
            raise SvgSpecError(f"{name} CSS values must not contain at-rules")
        if "\\" in value:
            raise SvgSpecError(f"{name} CSS values must not contain escapes")
        _validate_xml_characters(key, f"{name} CSS property")
        _validate_xml_characters(value, f"{name} CSS value")
        _validate_css_functions(value, name)


def validate_paint(value: str, name: str) -> None:
    """データ由来のfill/strokeを単色の字句文法で検証する。

    16進色、英字の色キーワード、none等のキーワード、数値だけを引数に
    持つrgb(a)/hsl(a)を許す。CSSの全ての色構文の解釈はしない。
    """
    validate_style({"fill": value}, name)
    if len(value) > _MAX_PAINT_LENGTH or not _PAINT_RE.fullmatch(value.strip()):
        raise SvgSpecError(f"{name} paint must be a single color or paint keyword")


def style_text(style: Mapping[str, str]) -> str:
    """辞書を安定した順序のinline CSSへ変換する。"""
    return ";".join(f"{key}:{value}" for key, value in style.items()) + (
        ";" if style else ""
    )


def merged_style(defaults: Mapping[str, str], supplied: Mapping[str, str]) -> str:
    """標準値へ指定値を重ねてinline CSSへ変換する。"""
    values = dict(defaults)
    values.update(supplied)
    return style_text(values)
