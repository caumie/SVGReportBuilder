"""見積・発注・請求・納品で使い回す取引文書テンプレート。

4種類の帳票は同じ枠と同じフィールド構造を使い、文書種別に応じて
タイトル、ラベル、要約、明細の「参照」列、合計欄の内容だけをデータで変える。
見積書なら参照=単価・金額、納品書なら参照=ロット・確認という具合に、
帳票の差分をレイアウトの複製ではなく値とラベルの差分として表現する。
"""

from collections.abc import Mapping
from pathlib import Path

from svgreportbuilder import FixedSlots, ImageField, SvgReportTemplate, TextField

TEXT = {
    "font-family": '"Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif',
    "font-size": "3.1px",
    "line-height": "1.4",
    "color": "#000",
    "padding": "1px 1.3px",
    "white-space": "pre-wrap",
    "overflow-wrap": "anywhere",
}
MONOSPACE = '"Noto Sans Mono CJK JP", monospace'
SMALL = TEXT | {"font-size": "2.6px", "line-height": "1.35"}
LABEL = SMALL | {"font-weight": "700"}
TITLE = TEXT | {"font-size": "7px", "font-weight": "700", "line-height": "1.2"}
PARTY = TEXT | {"font-size": "4px", "font-weight": "700"}
CENTER = TEXT | {
    "display": "flex", "align-items": "center", "justify-content": "center",
    "text-align": "center", "padding": "0.5px",
}
NUMERIC = TEXT | {
    "font-family": MONOSPACE, "font-variant-numeric": "tabular-nums",
}
CENTER_NUMERIC = NUMERIC | {
    "display": "flex", "align-items": "center", "justify-content": "center",
    "text-align": "center", "padding": "0.5px",
}
NUMBER = NUMERIC | {"text-align": "right", "white-space": "nowrap"}
IDENTIFIER = SMALL | {"font-family": MONOSPACE, "white-space": "nowrap"}
AMOUNT = NUMBER | {"font-size": "4.8px", "font-weight": "700", "padding": "0.5px 1.5px"}


def _field(
    target_id: str,
    value_path: str,
    style: Mapping[str, str],
    *,
    default: str | None = None,
) -> TextField:
    if default is None:
        return TextField(target_id=target_id, value_path=value_path, container_style=style)
    return TextField(
        target_id=target_id,
        value_path=value_path,
        container_style=style,
        default=default,
    )


svg_report_template = SvgReportTemplate(
    svg=Path(__file__).with_name("template.svg").read_text(encoding="utf-8"),
    fields=[
        _field("document_series_label_box", "document.series_label", SMALL),
        _field("document_title_box", "document.title", TITLE),
        _field("document_subtitle_box", "document.subtitle", SMALL, default=""),
        _field("document_number_label_box", "document.number_label", LABEL),
        _field("document_number_box", "document.number", IDENTIFIER),
        _field("document_date_label_box", "document.date_label", LABEL),
        _field("document_date_box", "document.date", CENTER_NUMERIC),
        _field("document_related_label_box", "document.related_label", LABEL),
        _field("document_related_box", "document.related_number", IDENTIFIER, default=""),
        _field("document_copy_box", "document.copy_label", SMALL, default=""),
        ImageField(
            target_id="document_barcode_box", value_path="document.barcode", default=None,
            container_style={"padding": "0.5px"}, image_style={"object-fit": "contain"},
        ),
        _field("document_readable_id_label_box", "document.readable_id_label", SMALL),
        _field("document_readable_id_box", "document.readable_id", IDENTIFIER),
        _field("page_label_box", "page.label", SMALL),
        _field("page_current_box", "page.current", CENTER_NUMERIC),
        _field("page_total_box", "page.total", CENTER_NUMERIC),
        _field("party_recipient_label_box", "party.recipient_label", LABEL),
        _field("party_recipient_name_box", "party.recipient_name", PARTY),
        _field("party_recipient_address_box", "party.recipient_address", TEXT),
        _field("party_issuer_label_box", "party.issuer_label", LABEL),
        _field("party_issuer_name_box", "party.issuer_name", PARTY),
        _field("party_issuer_address_box", "party.issuer_address", TEXT),
        _field("party_issuer_contact_box", "party.issuer_contact", SMALL, default=""),
        _field("summary_primary_label_box", "summary.primary_label", LABEL),
        _field("summary_primary_box", "summary.primary", AMOUNT),
        _field("summary_secondary_label_box", "summary.secondary_label", LABEL),
        _field("summary_secondary_box", "summary.secondary", CENTER_NUMERIC),
        _field("summary_tertiary_label_box", "summary.tertiary_label", LABEL),
        _field("summary_tertiary_box", "summary.tertiary", IDENTIFIER),
        _field("detail_heading_box", "detail.heading", LABEL),
        _field("detail_note_box", "detail.note", SMALL, default=""),
        _field("detail_header_no_box", "detail.headers.no", LABEL),
        _field("detail_header_code_box", "detail.headers.code", LABEL),
        _field("detail_header_description_box", "detail.headers.description", LABEL),
        _field("detail_header_quantity_box", "detail.headers.quantity", LABEL),
        _field("detail_header_unit_box", "detail.headers.unit", LABEL),
        _field("detail_header_reference_box", "detail.headers.reference", LABEL),
        _field("detail_header_amount_box", "detail.headers.amount", LABEL),
        FixedSlots(
            value_path="items", capacity=10, index="row",
            fields=[
                _field("detail_item_{row}_no_box", "line_number", CENTER_NUMERIC),
                _field("detail_item_{row}_code_box", "code", IDENTIFIER, default=""),
                _field("detail_item_{row}_description_box", "description", TEXT),
                _field("detail_item_{row}_quantity_box", "quantity", NUMBER, default=""),
                _field("detail_item_{row}_unit_box", "unit", CENTER, default=""),
                _field("detail_item_{row}_reference_box", "reference", IDENTIFIER, default=""),
                _field("detail_item_{row}_amount_box", "amount", NUMBER, default=""),
            ],
        ),
        _field("terms_label_box", "terms.label", LABEL),
        _field("terms_box", "terms.body", TEXT, default=""),
        FixedSlots(
            value_path="totals.rows", capacity=4, index="row", min_items=1,
            fields=[
                _field("total_{row}_label_box", "label", LABEL),
                _field("total_{row}_value_box", "value", NUMBER, default=""),
            ],
        ),
    ],
)

# 同じ svg_report_template に渡す値だけを切り替える4つの出力プロファイル。
# 呼び出し側はこの表を使って document / summary / detail / terms を組み立て、
# items の reference と amount に「単価・金額」または「ロット・受領」を入れる。
DOCUMENT_PROFILES: dict[str, dict[str, str]] = {
    "quotation": {
        "title": "見積書", "date_label": "発行日", "primary_label": "見積総額（税込）",
        "secondary_label": "有効期限", "tertiary_label": "納期・実施時期",
        "detail_heading": "01  見積明細", "reference_header": "単価", "amount_header": "金額",
        "terms_label": "02  見積条件・対象範囲・除外事項",
    },
    "purchase_order": {
        "title": "発注書", "date_label": "発注日", "primary_label": "発注総額（税込）",
        "secondary_label": "指定納期", "tertiary_label": "案件番号",
        "detail_heading": "01  発注明細", "reference_header": "単価", "amount_header": "金額",
        "terms_label": "02  納入・支払条件",
    },
    "invoice": {
        "title": "請求書", "date_label": "請求日", "primary_label": "今回ご請求額（税込）",
        "secondary_label": "支払期日", "tertiary_label": "登録番号",
        "detail_heading": "01  請求明細", "reference_header": "単価・税率", "amount_header": "金額",
        "terms_label": "02  振込先・連絡事項",
    },
    "delivery_note": {
        "title": "納品書", "date_label": "納品日", "primary_label": "納品数量",
        "secondary_label": "納品日", "tertiary_label": "受注番号",
        "detail_heading": "01  納品明細", "reference_header": "ロット・製造番号", "amount_header": "受領",
        "terms_label": "02  連絡事項・受領確認",
    },
}
