"""レンダラーが生成する単純なinline CSSの扱い。"""

from __future__ import annotations

import re
from collections.abc import Mapping

from .models import SvgSpecError

# 機能の塊: CSSは完全解釈せず、1値1宣言だけを許可する。
# セミコロンを値に許可しないため、引用符・コメント・関数を解析する必要がない。
_PROPERTY_RE = re.compile(
    r"^(?:--[A-Za-z0-9_-]+|-[A-Za-z_][A-Za-z0-9_-]*|[A-Za-z_][A-Za-z0-9_-]*)$"
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


def validate_style(style: Mapping[str, str], name: str) -> None:
    """style辞書を検証する。既存SVGのstyle属性は解析しない。"""
    for key, value in style.items():
        if not _PROPERTY_RE.fullmatch(key):
            raise SvgSpecError(f"{name} contains an invalid CSS property {key!r}")
        if ";" in value:
            raise SvgSpecError(f"{name} CSS values must not contain ';'")
        _validate_xml_characters(key, f"{name} CSS property")
        _validate_xml_characters(value, f"{name} CSS value")


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
