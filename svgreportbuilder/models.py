"""SVGレポート生成で使う公開データ型。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias, cast

if TYPE_CHECKING:
    from .renderer import PreparedReport


# 機能の塊: 呼び出し側が判別できる例外階層を定義する。
class SvgRenderError(Exception):
    """SVGレポート生成に関する基底例外。"""


class SvgSpecError(SvgRenderError):
    """フィールド定義が不正な場合の例外。"""


class SvgTemplateError(SvgRenderError):
    """SVGテンプレートが対応範囲外の場合の例外。"""


class SvgDataError(SvgRenderError):
    """入力データがフィールド定義を満たさない場合の例外。"""


# 機能の塊: 欠損値と画像入力の表現を定義する。
class UnsetType(Enum):
    UNSET = "unset"

    def __repr__(self) -> str:
        return "UNSET"

    def __str__(self) -> str:
        return "UNSET"


UNSET = UnsetType.UNSET


@dataclass(frozen=True, kw_only=True)
class ImageSource:
    """出力へ埋め込む画像のバイト列とMIMEを持つ値。"""

    data: bytes
    mime_type: str


TextValue: TypeAlias = str | int | float | bool | None
DataValue: TypeAlias = (
    TextValue
    | ImageSource
    | Mapping[str, "DataValue"]
    | list["DataValue"]
    | tuple["DataValue", ...]
)
Data: TypeAlias = Mapping[str, DataValue]


# 機能の塊: styleは入力辞書をスナップショット化してから保持する。
def _style_snapshot(style: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(cast(object, style), Mapping):
        raise SvgSpecError("style must be a mapping")
    return MappingProxyType(dict(style))


@dataclass(frozen=True, kw_only=True)
class TextField:
    """rectの領域へプレーンテキストを差し込む定義。"""

    target_id: str
    value_path: str
    default: TextValue | UnsetType = UNSET
    container_style: Mapping[str, str] = field(default_factory=lambda: {})
    foreign_object_style: Mapping[str, str] = field(default_factory=lambda: {})
    hide_target: bool = False
    remove_stroke: bool = False
    target_fill_path: str | None = None
    target_stroke_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "container_style", _style_snapshot(self.container_style)
        )
        object.__setattr__(
            self, "foreign_object_style", _style_snapshot(self.foreign_object_style)
        )


@dataclass(frozen=True, kw_only=True)
class ImageField:
    """rectの領域へData URI画像を差し込む定義。"""

    target_id: str
    value_path: str
    default: ImageSource | None | UnsetType = UNSET
    container_style: Mapping[str, str] = field(default_factory=lambda: {})
    image_style: Mapping[str, str] = field(default_factory=lambda: {})
    foreign_object_style: Mapping[str, str] = field(default_factory=lambda: {})
    hide_target: bool = False
    remove_stroke: bool = False
    target_fill_path: str | None = None
    target_stroke_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "container_style", _style_snapshot(self.container_style)
        )
        object.__setattr__(self, "image_style", _style_snapshot(self.image_style))
        object.__setattr__(
            self, "foreign_object_style", _style_snapshot(self.foreign_object_style)
        )


FieldSpec: TypeAlias = TextField | ImageField

FieldFactory: TypeAlias = Callable[[int], TextField | ImageField]


@dataclass(frozen=True, kw_only=True)
class FixedSlots:
    """配列をSVGに用意した固定枠へ割り当てる定義。"""

    value_path: str
    capacity: int
    index: str
    fields: Sequence["FieldSpec | FixedSlots | FieldFactory"]
    min_items: int = 0

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.fields), Sequence) or isinstance(
            cast(object, self.fields), (str, bytes, bytearray)
        ):
            raise SvgSpecError("FixedSlots.fields must be a sequence")
        try:
            fields = tuple(self.fields)
        except TypeError as error:
            raise SvgSpecError("FixedSlots.fields must be a sequence") from error
        object.__setattr__(self, "fields", fields)


SlotDefinition: TypeAlias = FieldSpec | FixedSlots | FieldFactory
FieldDefinition: TypeAlias = FieldSpec | FixedSlots


@dataclass(frozen=True, kw_only=True)
class SvgReportTemplate:
    """SVG本体と差し込み定義をまとめた帳票テンプレート。"""

    svg: str
    fields: Sequence[FieldDefinition]
    prepared: PreparedReport = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.fields), Sequence) or isinstance(
            cast(object, self.fields), (str, bytes, bytearray)
        ):
            raise SvgSpecError("SvgReportTemplate.fields must be a sequence")
        try:
            fields = tuple(self.fields)
        except TypeError as error:
            raise SvgSpecError("SvgReportTemplate.fields must be a sequence") from error
        object.__setattr__(self, "fields", fields)
        from .renderer import prepare_report

        object.__setattr__(self, "prepared", prepare_report(self))

    def render(self, data: Data) -> str:
        from .renderer import render_report

        return render_report(self, data)
