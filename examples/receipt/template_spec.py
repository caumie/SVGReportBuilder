"""領収書の記載項目と固定枠の対応。

共通仕様: 白地・黒線、mm座標、本文3.1mm、罫線0.22mm／見出し線0.5mm。
文書区分 document.copy_label（原本・控など）と page.current / page.total は別管理。
日付・金額・番号は表示用に整形した値を受け取り、計算や採番は行わない。
document.readable_id は document.barcode の符号化内容と同じ値を渡す。
明細の分割、頁番号、全体を通した行番号の設定は呼び出し側で行う。
任意欄は欠落時に空欄。固定枠を超える文章には枠・文字サイズの調整が必要。
単票は page.current=1 / page.total=1 を呼び出し側で指定する。
受領済みの金額・日付を表示する欄であり、決済機能は持たない。
"""

from pathlib import Path

from svgreportbuilder import ImageField, SvgReportTemplate, TextField

# viewBoxの1単位は1mm。CSSのpx値もこの座標系で指定する。
TEXT = {
    "font-family": '"Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif',
    "font-size": "3.1px",
    "line-height": "1.4",
    "color": "#000",
    "padding": "1px 1.3px",
    "white-space": "pre-wrap",
    "overflow-wrap": "anywhere",
}
SMALL = TEXT | {"font-size": "2.7px", "line-height": "1.4"}
BOLD = TEXT | {"font-weight": "700"}
PARTY = BOLD | {"font-size": "4px"}
CENTER = TEXT | {
    "display": "flex", "align-items": "center", "justify-content": "center",
    "text-align": "center", "padding": "0.6px",
}
NUMBER = TEXT | {
    "text-align": "right", "font-variant-numeric": "tabular-nums",
    "white-space": "nowrap",
}
IDENTIFIER = SMALL | {"font-family": '"Noto Sans Mono CJK JP", monospace', "line-height": "1.35"}
AMOUNT = NUMBER | {"font-size": "5.4px", "font-weight": "700", "padding": "0.5px 2px"}

svg_report_template = SvgReportTemplate(
    svg=Path(__file__).with_name("template.svg").read_text(encoding="utf-8"),
    fields=[
        ImageField(
            target_id="issuer_logo_box", value_path="issuer.logo",
            default=None, container_style={"padding": "0.5px"},
            image_style={"object-fit": "contain"},
        ),
        TextField(
            target_id="document_copy_box", value_path="document.copy_label",
            container_style=TEXT, default='',
        ),
        TextField(
            target_id="document_number_box", value_path="document.number",
            container_style=IDENTIFIER,
        ),
        TextField(
            target_id="document_date_box", value_path="document.date",
            container_style=CENTER,
        ),
        TextField(
            target_id="reference_number_box", value_path="document.reference_number",
            container_style=IDENTIFIER, default='',
        ),
        # 実際のバーコード画像を渡す。符号化・画像生成は呼び出し側の責務。
        # 画像自体にも規格に必要な余白を含め、この枠では縦横比を維持する。
        ImageField(
            target_id="document_barcode_box", value_path="document.barcode",
            default=None, container_style={"padding": "0.5px"},
            image_style={"object-fit": "contain"},
        ),
        TextField(
            target_id="document_readable_id_box", value_path="document.readable_id",
            container_style=IDENTIFIER,
        ),
        TextField(
            target_id="page_current_box", value_path="page.current",
            container_style=CENTER,
        ),
        TextField(
            target_id="page_total_box", value_path="page.total",
            container_style=CENTER,
        ),
        TextField(
            target_id="recipient_name_box", value_path="recipient.name",
            container_style=PARTY,
        ),
        TextField(
            target_id="received_amount_box", value_path="receipt.amount",
            container_style=AMOUNT,
        ),
        TextField(
            target_id="purpose_box", value_path="receipt.purpose",
            container_style=TEXT,
        ),
        TextField(
            target_id="payment_method_box", value_path="receipt.payment_method",
            container_style=TEXT,
        ),
        TextField(
            target_id="issuer_name_box", value_path="issuer.name",
            container_style=BOLD,
        ),
        TextField(
            target_id="issuer_address_box", value_path="issuer.address",
            container_style=SMALL,
        ),
        TextField(
            target_id="issuer_contact_box", value_path="issuer.contact",
            container_style=SMALL,
        ),
        TextField(
            target_id="issuer_registration_box", value_path="issuer.registration_number",
            container_style=IDENTIFIER,
        ),
        TextField(
            target_id="tax_amount_box", value_path="receipt.tax_amount",
            container_style=NUMBER,
        ),
    ],
)
