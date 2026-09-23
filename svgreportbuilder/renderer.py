"""固定SVGテンプレートへテキストと画像を差し込む。"""

from __future__ import annotations

import base64
import inspect
import re
import string
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import TypeAlias, cast

from .css import merged_style, style_text, validate_paint, validate_style
from .models import (
    UNSET,
    Data,
    DataValue,
    FieldDefinition,
    FieldFactory,
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
XHTML_NS = "http://www.w3.org/1999/xhtml"
_LENGTH_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:cm|mm|in|pt|pc|px)?$")
_MIME_RE = re.compile(r"^image/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*$", re.IGNORECASE)
_INDEX_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_RENDERED_ANCESTORS = frozenset(
    f"{{{SVG_NS}}}{name}" for name in ("svg", "g", "a")
)

ET.register_namespace("", SVG_NS)
ET.register_namespace("html", XHTML_NS)

DEFAULT_CONTAINER_STYLE = {
    "width": "100%",
    "height": "100%",
    "box-sizing": "border-box",
}
DEFAULT_IMAGE_STYLE = {
    "display": "block",
    "width": "100%",
    "height": "100%",
    "object-fit": "contain",
}
FIELD_CLASS = "svgrb-field"
CONTAINER_CLASS = "svgrb-container"
IMAGE_CLASS = "svgrb-image"


def _svg_tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def _html_tag(name: str) -> str:
    return f"{{{XHTML_NS}}}{name}"


def _validate_xml_characters(
    value: str, context: str, error_type: type[Exception]
) -> None:
    for index, character in enumerate(value):
        codepoint = ord(character)
        if not (
            codepoint in (0x9, 0xA, 0xD)
            or 0x20 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        ):
            raise error_type(
                f"{context} contains an XML 1.0 forbidden character "
                f"U+{codepoint:04X} at index {index}"
            )


class _PathMissing(Exception):
    pass


PathPart = str | int
ArrayValidationKey: TypeAlias = tuple[tuple[PathPart, ...], int, int]


def _parse_path(path: str, name: str) -> tuple[bool, tuple[str, ...]]:
    if not isinstance(cast(object, path), str):
        raise SvgSpecError(f"{name} must be a string")
    if not path:
        raise SvgSpecError(f"{name} must not be empty")
    absolute = path.startswith("$.")
    if path == "$" or (path.startswith("$") and not absolute):
        raise SvgSpecError(f"{name} must use '$.' for an absolute path")
    body = path[2:] if absolute else path
    parts = tuple(body.split("."))
    if any(not part for part in parts):
        raise SvgSpecError(f"{name} {path!r} must not contain empty path components")
    _validate_xml_characters(path, name, SvgSpecError)
    return absolute, parts


def _component(value: str) -> PathPart:
    # Mappingでは数字も文字列キーとして扱い、list/tupleでだけ添字に変換する。
    return value


def _join_path(
    context: tuple[PathPart, ...], path: str, name: str
) -> tuple[PathPart, ...]:
    absolute, parts = _parse_path(path, name)
    parsed = tuple(_component(part) for part in parts)
    return parsed if absolute else context + parsed


def _path_text(path: Sequence[PathPart]) -> str:
    return ".".join(str(part) for part in path)


def _lookup(data: DataValue, path: Sequence[PathPart]) -> DataValue:
    current = data
    for part in path:
        if isinstance(current, Mapping):
            if not isinstance(part, str) or part not in current:
                raise _PathMissing(_path_text(path))
            current = current[part]
        elif isinstance(current, (list, tuple)):
            if isinstance(part, str) and part.isdigit():
                index = int(part)
            elif isinstance(part, int):
                index = part
            else:
                raise _PathMissing(_path_text(path))
            try:
                current = current[index]
            except IndexError as error:
                raise _PathMissing(_path_text(path)) from error
        else:
            raise _PathMissing(_path_text(path))
    return current


@dataclass(frozen=True)
class _SlotRef:
    array_path: tuple[PathPart, ...]
    index: int
    capacity: int
    min_items: int
    description: str


@dataclass(frozen=True)
class _ExpandedField:
    field: FieldSpec
    context_path: tuple[PathPart, ...]
    slots: tuple[_SlotRef, ...]
    value_path: str


@dataclass(frozen=True)
class _SlotValidation:
    slots: tuple[_SlotRef, ...]


PreparedOperation: TypeAlias = _ExpandedField | _SlotValidation


@dataclass(frozen=True)
class PreparedReport:
    operations: tuple[PreparedOperation, ...]


def _expand_target_id(target_id: str, bindings: Mapping[str, int], context: str) -> str:
    if not isinstance(cast(object, target_id), str):
        raise SvgSpecError(f"{context} target_id must be a string")
    if not target_id:
        raise SvgSpecError(f"{context} target_id must not be empty")
    _validate_xml_characters(target_id, f"{context} target_id", SvgSpecError)
    formatter = string.Formatter()
    try:
        parsed = tuple(formatter.parse(target_id))
    except ValueError as error:
        raise SvgSpecError(f"{context} target_id has invalid braces") from error
    for _, field_name, format_spec, conversion in parsed:
        if field_name is None:
            continue
        if not _INDEX_RE.fullmatch(field_name) or format_spec or conversion:
            raise SvgSpecError(
                f"{context} target_id may contain only simple index placeholders"
            )
        if field_name not in bindings:
            raise SvgSpecError(
                f"{context} target_id refers to unknown index {field_name!r}"
            )
    try:
        result = target_id.format_map(dict(bindings))
    except (KeyError, ValueError) as error:
        raise SvgSpecError(f"{context} target_id has invalid placeholders") from error
    _validate_xml_characters(result, f"{context} target_id", SvgSpecError)
    return result


def _validate_field(field: FieldSpec, context: str) -> None:
    _parse_path(field.value_path, f"{context}.value_path")
    for name in ("hide_target", "remove_stroke"):
        if not isinstance(getattr(field, name), bool):
            raise SvgSpecError(f"{context}.{name} must be a bool")
    for name in ("target_fill_path", "target_stroke_path"):
        value = getattr(field, name)
        if value is not None:
            _parse_path(value, f"{context}.{name}")
    validate_style(field.container_style, f"{context}.container_style")
    validate_style(field.foreign_object_style, f"{context}.foreign_object_style")
    if isinstance(field, ImageField):
        validate_style(field.image_style, f"{context}.image_style")


def _expand_definitions(
    definitions: Sequence[FieldDefinition | FieldFactory],
    *,
    context_path: tuple[PathPart, ...],
    slots: tuple[_SlotRef, ...],
    bindings: Mapping[str, int],
    location: str,
) -> list[PreparedOperation]:
    expanded: list[PreparedOperation] = []
    for position, definition in enumerate(definitions):
        here = f"{location}.fields[{position}]"
        if isinstance(definition, FixedSlots):
            if (
                not isinstance(cast(object, definition.capacity), int)
                or isinstance(definition.capacity, bool)
                or definition.capacity <= 0
            ):
                raise SvgSpecError(f"{here}.capacity must be a positive integer")
            if (
                not isinstance(cast(object, definition.min_items), int)
                or isinstance(definition.min_items, bool)
                or not 0 <= definition.min_items <= definition.capacity
            ):
                raise SvgSpecError(
                    f"{here}.min_items must be an integer between 0 and capacity"
                )
            if not isinstance(cast(object, definition.index), str) or not _INDEX_RE.fullmatch(
                definition.index
            ):
                raise SvgSpecError(f"{here}.index is not a valid index name")
            if definition.index in bindings:
                raise SvgSpecError(
                    f"{here}.index {definition.index!r} shadows an ancestor index"
                )
            array_path = _join_path(
                context_path, definition.value_path, f"{here}.value_path"
            )
            if not definition.fields:
                expanded.append(
                    _SlotValidation(
                        slots=slots
                        + (
                            _SlotRef(
                                array_path=array_path,
                                index=0,
                                capacity=definition.capacity,
                                min_items=definition.min_items,
                                description=f"{here} ({definition.value_path!r}, index 0)",
                            ),
                        )
                    )
                )
                continue
            for index in range(definition.capacity):
                slot = _SlotRef(
                    array_path=array_path,
                    index=index,
                    capacity=definition.capacity,
                    min_items=definition.min_items,
                    description=f"{here} ({definition.value_path!r}, index {index})",
                )
                child_bindings = dict(bindings)
                child_bindings[definition.index] = index
                expanded.extend(
                    _expand_definitions(
                        definition.fields,
                        context_path=array_path + (index,),
                        slots=slots + (slot,),
                        bindings=child_bindings,
                        location=f"{here}[{index}]",
                    )
                )
            continue
        if callable(definition):
            if not slots:
                raise SvgSpecError(
                    f"{here} field functions are only valid inside FixedSlots"
                )
            if inspect.iscoroutinefunction(definition):
                raise SvgSpecError(f"{here} field function must be synchronous")
            slot_index = slots[-1].index
            try:
                generated = definition(slot_index)
            except Exception as error:
                raise SvgSpecError(
                    f"{here} field function failed for index {slot_index}"
                ) from error
            definition = generated
        if not isinstance(cast(object, definition), (TextField, ImageField)):
            raise SvgSpecError(f"{here} must be a TextField, ImageField, or FixedSlots")
        _validate_field(definition, here)
        target_id = _expand_target_id(definition.target_id, bindings, here)
        field = replace(definition, target_id=target_id)
        field_path = _join_path(context_path, field.value_path, f"{here}.value_path")
        expanded.append(
            _ExpandedField(
                field=field,
                context_path=context_path,
                slots=slots,
                value_path=_path_text(field_path),
            )
        )
    return expanded


def _index_template(
    root: ET.Element,
) -> tuple[dict[str, ET.Element], dict[ET.Element, ET.Element]]:
    elements: dict[str, ET.Element] = {}
    parents = {child: parent for parent in root.iter() for child in parent}
    for element in root.iter():
        element_id = element.get("id")
        if not element_id:
            continue
        if element_id in elements:
            raise SvgTemplateError(f"duplicate SVG id {element_id!r}")
        elements[element_id] = element
    return elements, parents


def _validate_length(value: str | None, target_id: str, name: str) -> None:
    if value is None or not _LENGTH_RE.fullmatch(value.strip()):
        raise SvgTemplateError(
            f"target id {target_id!r} has an invalid {name} length {value!r}; "
            "use a number or an absolute SVG unit"
        )
    numeric = re.sub(r"(?:cm|mm|in|pt|pc|px)$", "", value.strip())
    try:
        number = Decimal(numeric)
    except InvalidOperation as error:  # pragma: no cover
        raise SvgTemplateError(
            f"target id {target_id!r} has an invalid {name} length"
        ) from error
    if name in ("width", "height") and number <= 0:
        raise SvgTemplateError(
            f"target id {target_id!r} must have a positive {name} length"
        )


def prepare_report(report: SvgReportTemplate) -> PreparedReport:
    if not isinstance(cast(object, report.svg), str):
        raise SvgTemplateError("svg must be a string")
    try:
        root = ET.fromstring(report.svg)
    except ET.ParseError as error:
        raise SvgTemplateError("svg is not well-formed XML") from error
    if root.tag != _svg_tag("svg"):
        raise SvgTemplateError("template root must be an svg element")
    expanded = _expand_definitions(
        report.fields,
        context_path=(),
        slots=(),
        bindings={},
        location="report",
    )
    elements, parents = _index_template(root)
    target_ids: set[str] = set()
    for item in expanded:
        if isinstance(item, _SlotValidation):
            continue
        if item.field.target_id in target_ids:
            raise SvgSpecError(f"duplicate target_id {item.field.target_id!r}")
        target_ids.add(item.field.target_id)
    for item in expanded:
        if isinstance(item, _SlotValidation):
            continue
        field = item.field
        target = elements.get(field.target_id)
        if target is None:
            raise SvgTemplateError(f"target id {field.target_id!r} was not found")
        if target.tag != _svg_tag("rect"):
            raise SvgTemplateError(
                f"target id {field.target_id!r} must identify a rect"
            )
        if target.get("transform") is not None:
            raise SvgTemplateError(
                f"target id {field.target_id!r} must not have transform"
            )
        missing = [
            name for name in ("x", "y", "width", "height") if target.get(name) is None
        ]
        if missing:
            raise SvgTemplateError(
                f"target id {field.target_id!r} is missing {', '.join(missing)}"
            )
        for name in ("x", "y", "width", "height"):
            _validate_length(target.get(name), field.target_id, name)
        ancestor = parents.get(target)
        while ancestor is not None:
            if ancestor.tag not in _RENDERED_ANCESTORS:
                raise SvgTemplateError(
                    f"target id {field.target_id!r} is inside a non-rendered "
                    "or unsupported SVG container"
                )
            ancestor = parents.get(ancestor)
    return PreparedReport(tuple(expanded))


def _validate_array(root: Data, slot: _SlotRef) -> Sequence[DataValue]:
    try:
        value = _lookup(root, slot.array_path)
    except _PathMissing as error:
        raise SvgDataError(
            f"fixed slots path {_path_text(slot.array_path)!r} was not found"
        ) from error
    if not isinstance(value, (list, tuple)):
        raise SvgDataError(
            f"fixed slots path {_path_text(slot.array_path)!r} must resolve to a list or tuple"
        )
    if len(value) < slot.min_items or len(value) > slot.capacity:
        raise SvgDataError(
            f"fixed slots path {_path_text(slot.array_path)!r} has {len(value)} items; "
            f"expected between {slot.min_items} and {slot.capacity}"
        )
    for item in value:
        if not isinstance(item, Mapping):
            raise SvgDataError(
                f"fixed slots path {_path_text(slot.array_path)!r} must contain mappings"
            )
    return value


def _resolve_slot_state(
    root: Data,
    slots: tuple[_SlotRef, ...],
    validated_lengths: dict[ArrayValidationKey, int],
) -> bool:
    active = True
    for slot in slots:
        if not active:
            break
        key = (slot.array_path, slot.capacity, slot.min_items)
        length = validated_lengths.get(key)
        if length is None:
            length = len(_validate_array(root, slot))
            validated_lengths[key] = length
        if slot.index >= length:
            active = False
    return active


def _data_value(root: Data, item: _ExpandedField, active: bool) -> DataValue:
    if not active:
        return None
    path = _join_path(item.context_path, item.field.value_path, "value_path")
    try:
        return _lookup(root, path)
    except _PathMissing as error:
        if item.field.default is not UNSET:
            return item.field.default
        raise SvgDataError(
            f"value_path {item.value_path!r} for {item.field.target_id!r} was not found"
        ) from error


def _target_paint_value(
    root: Data, item: _ExpandedField, path: str, property_name: str
) -> str | None:
    target_path = _join_path(
        item.context_path, path, f"{item.field.target_id}.{property_name}_path"
    )
    try:
        value = _lookup(root, target_path)
    except _PathMissing as error:
        raise SvgDataError(
            f"target {property_name} path {_path_text(target_path)!r} for {item.field.target_id!r} was not found"
        ) from error
    if value is None:
        return None
    if not isinstance(value, str):
        raise SvgDataError(
            f"target {property_name} path {_path_text(target_path)!r} for {item.field.target_id!r} must resolve to a string or None"
        )
    try:
        validate_paint(value, f"target {item.field.target_id!r}")
    except SvgSpecError as error:
        raise SvgDataError(
            f"target {property_name} value for {item.field.target_id!r} is not valid CSS"
        ) from error
    return value


def _validated_mime_type(value: str, context: str) -> str:
    if not isinstance(cast(object, value), str) or not _MIME_RE.fullmatch(value):
        raise SvgDataError(f"{context} image MIME type is invalid")
    _validate_xml_characters(value, f"{context} image MIME type", SvgDataError)
    return value


def _image_data_uri(source: ImageSource, *, context: str) -> str:
    mime_type = _validated_mime_type(source.mime_type, context)
    if not isinstance(cast(object, source.data), bytes):
        raise SvgDataError(f"{context} image data must be bytes")
    return f"data:{mime_type};base64,{base64.b64encode(source.data).decode('ascii')}"


def _field_element(
    root: Data, item: _ExpandedField, target: ET.Element, active: bool
) -> ET.Element:
    field = item.field
    field_kind = "text" if isinstance(field, TextField) else "image"
    foreign_object = ET.Element(
        _svg_tag("foreignObject"),
        {
            **{name: target.attrib[name] for name in ("x", "y", "width", "height")},
            "class": FIELD_CLASS,
            "data-svgrb-target": field.target_id,
            "data-svgrb-kind": field_kind,
            "data-svgrb-role": "field",
            "data-svgrb-value-path": item.value_path,
        },
    )
    if field.foreign_object_style:
        foreign_object.set("style", style_text(field.foreign_object_style))
    div = ET.SubElement(
        foreign_object,
        _html_tag("div"),
        {
            "class": CONTAINER_CLASS,
            "data-svgrb-role": "container",
            "style": merged_style(DEFAULT_CONTAINER_STYLE, field.container_style),
        },
    )
    value = _data_value(root, item, active)
    if isinstance(field, TextField):
        if value is None:
            text = ""
        elif isinstance(value, (str, int, float, bool)):
            text = str(value)
        else:
            raise SvgDataError(
                f"value_path {item.value_path!r} for {field.target_id!r} must resolve to a text value"
            )
        _validate_xml_characters(
            text,
            f"value_path {item.value_path!r} for {field.target_id!r}",
            SvgDataError,
        )
        div.text = text
    elif active and value is not None:
        if not isinstance(value, ImageSource):
            raise SvgDataError(
                f"value_path {item.value_path!r} for {field.target_id!r} must resolve to None or an ImageSource"
            )
        ET.SubElement(
            div,
            _html_tag("img"),
            {
                "class": IMAGE_CLASS,
                "data-svgrb-role": "image",
                "src": _image_data_uri(
                    value,
                    context=f"value_path {item.value_path!r} for {field.target_id!r}",
                ),
                "style": merged_style(DEFAULT_IMAGE_STYLE, field.image_style),
            },
        )
    return foreign_object


def render_report(report: SvgReportTemplate, data: Data) -> str:
    if not isinstance(cast(object, data), Mapping):
        raise SvgDataError("data must be a mapping")
    prepared = report.prepared
    root = ET.fromstring(report.svg)
    elements, parents = _index_template(root)
    validated_lengths: dict[ArrayValidationKey, int] = {}
    generated_by_target: dict[ET.Element, ET.Element] = {}
    affected_parents: set[ET.Element] = set()
    for operation in prepared.operations:
        if isinstance(operation, _SlotValidation):
            _resolve_slot_state(data, operation.slots, validated_lengths)
            continue
        item = operation
        target = elements[item.field.target_id]
        parent = parents[target]
        active = _resolve_slot_state(data, item.slots, validated_lengths)
        if item.field.hide_target:
            target.set("visibility", "hidden")
        target_paint: dict[str, str] = {}
        if active and item.field.target_fill_path is not None:
            fill = _target_paint_value(data, item, item.field.target_fill_path, "fill")
            if fill is not None:
                target_paint["fill"] = fill
        if active and item.field.target_stroke_path is not None:
            stroke = _target_paint_value(
                data, item, item.field.target_stroke_path, "stroke"
            )
            if stroke is not None:
                target_paint["stroke"] = stroke
        if item.field.remove_stroke:
            target_paint["stroke"] = "none"
        if target_paint:
            existing_style = target.get("style", "")
            if existing_style and not existing_style.endswith(";"):
                existing_style += ";"
            target.set("style", existing_style + style_text(target_paint))
        generated_by_target[target] = _field_element(data, item, target, active)
        affected_parents.add(parent)
    for parent in affected_parents:
        children: list[ET.Element] = []
        for child in parent:
            children.append(child)
            generated = generated_by_target.get(child)
            if generated is not None:
                children.append(generated)
        parent[:] = children
    # XML整形の空白は、XHTMLのwhite-space指定によって表示内容になる。
    return ET.tostring(root, encoding="unicode", xml_declaration=False)
