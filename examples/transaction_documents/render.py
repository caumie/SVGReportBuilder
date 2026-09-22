"""共通テンプレートから4種類の取引文書を生成する。

見積・発注・請求・納品の違いはレイアウトの複製ではなく、
DOCUMENT_PROFILES と文書データの差し替えで表現する。
"""

from __future__ import annotations

from pathlib import Path

from svgreportbuilder import Data, DataValue, ImageSource

from .template_spec import DOCUMENT_PROFILES, svg_report_template


OUTPUT_DIR = Path(__file__).parent
OUTPUT_NAMES = {
    "quotation": "output-quotation.svg",
    "purchase_order": "output-purchase-order.svg",
    "invoice": "output-invoice.svg",
    "delivery_note": "output-delivery-note.svg",
}


def barcode(value: str) -> ImageSource:
    """サンプル用のバーコード画像を作る。

    規格へのエンコードはこの例の責務ではないため、値をビット列へ展開した
    見本画像にしている。実運用では呼び出し側で Code 128 等を生成して渡す。
    """
    bits = "101011" + "".join(f"{byte:08b}0" for byte in value.encode("utf-8")) + "110101"
    bars: list[str] = []
    for index, bit in enumerate(bits):
        if bit == "1":
            bars.append(f'<rect x="{index + 8}" y="4" width="1" height="32"/>')
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" '
        f'viewBox="0 0 {len(bits) + 16} 40">'
        '<rect width="100%" height="100%" fill="white"/>'
        '<g fill="black">' + "".join(bars) + "</g></svg>"
    )
    return ImageSource(data=svg.encode("utf-8"), mime_type="image/svg+xml")


def item(
    line_number: int,
    code: str,
    description: str,
    quantity: str,
    unit: str,
    reference: str,
    amount: str,
) -> Data:
    return {
        "line_number": line_number,
        "code": code,
        "description": description,
        "quantity": quantity,
        "unit": unit,
        "reference": reference,
        "amount": amount,
    }


def document_data(kind: str) -> Data:
    profile = DOCUMENT_PROFILES[kind]
    document: dict[str, DataValue] = {
        "series_label": "01 REPORT / TRANSACTION DOCUMENT",
        "title": profile["title"],
        "subtitle": "共通テンプレートからの出力 / モノクロ運用帳票",
        "number_label": "文書番号",
        "date_label": profile["date_label"],
        "related_label": "関連番号",
        "copy_label": "原本",
        "barcode": None,
        "readable_id_label": "照合ID",
    }
    common: dict[str, DataValue] = {
        "document": document,
        "page": {"label": "頁 / 総頁", "current": 1, "total": 1},
        "detail": {
            "heading": profile["detail_heading"],
            "note": "金額・数量は表示用に整形済み / 固定10行",
            "headers": {
                "no": "No.",
                "code": "品目コード",
                "description": "内容・仕様",
                "quantity": "数量",
                "unit": "単位",
                "reference": profile["reference_header"],
                "amount": profile["amount_header"],
            },
        },
    }

    if kind == "quotation":
        number = "Q-2026-0018"
        document.update({
            "number": number, "date": "2026年9月20日", "related_number": "相談会-014",
            "readable_id": number, "barcode": barcode(number),
        })
        common.update({
            "party": {
                "recipient_label": "見積先",
                "recipient_name": "株式会社みらい産業 御中",
                "recipient_address": "〒100-0001\n東京都千代田区千代田1-1",
                "issuer_label": "発行者",
                "issuer_name": "サンプルソリューション株式会社",
                "issuer_address": "〒105-0001 東京都港区1-2-3",
                "issuer_contact": "営業部　03-0000-0000",
            },
            "summary": {
                "primary_label": profile["primary_label"], "primary": "418,000円",
                "secondary_label": profile["secondary_label"], "secondary": "30日間",
                "tertiary_label": profile["tertiary_label"], "tertiary": "2026年10月14日",
            },
            "items": [
                item(1, "SET-001", "業務システム初期設定", "1", "式", "300,000円", "300,000円"),
                item(2, "TRN-002", "操作研修（オンライン）", "2", "回", "50,000円", "100,000円"),
            ],
            "terms": {"label": profile["terms_label"], "body": "納期：ご発注から4週間\n仕様変更は別途お見積りとなります。"},
            "totals": {"rows": [
                {"label": "税抜小計", "value": "400,000円"}, {"label": "値引額", "value": "▲20,000円"},
                {"label": "消費税額", "value": "38,000円"}, {"label": "税込合計", "value": "418,000円"},
            ]},
        })
    elif kind == "purchase_order":
        number = "PO-2026-0042"
        document.update({
            "number": number, "date": "2026年9月20日", "related_number": "PJ-2026-14",
            "readable_id": number, "barcode": barcode(number),
        })
        common.update({
            "party": {
                "recipient_label": "発注先", "recipient_name": "東都オフィス株式会社 御中",
                "recipient_address": "〒135-0001\n東京都江東区1-4-8", "issuer_label": "発注者",
                "issuer_name": "サンプルソリューション株式会社", "issuer_address": "〒105-0001 東京都港区1-2-3",
                "issuer_contact": "購買担当　佐藤花子",
            },
            "summary": {
                "primary_label": profile["primary_label"], "primary": "220,000円",
                "secondary_label": profile["secondary_label"], "secondary": "2026年10月2日",
                "tertiary_label": profile["tertiary_label"], "tertiary": "PJ-2026-14",
            },
            "items": [
                item(1, "MON-101", "24インチモニター", "4", "台", "42,000円", "168,000円"),
                item(2, "ARM-204", "モニターアーム", "4", "台", "13,000円", "52,000円"),
            ],
            "terms": {"label": profile["terms_label"], "body": "納入先：本社3階 総務部\n納品時に担当者へ連絡してください。"},
            "totals": {"rows": [
                {"label": "商品計", "value": "220,000円"}, {"label": "送料", "value": "0円"},
                {"label": "消費税額", "value": "22,000円"}, {"label": "発注合計", "value": "242,000円"},
            ]},
        })
    elif kind == "invoice":
        number = "INV-2026-0091"
        document.update({
            "number": number, "date": "2026年9月20日", "related_number": "PO-2026-0042",
            "readable_id": number, "barcode": barcode(number),
        })
        common.update({
            "party": {
                "recipient_label": "請求先", "recipient_name": "株式会社みらい産業 御中",
                "recipient_address": "〒100-0001\n東京都千代田区千代田1-1", "issuer_label": "発行者",
                "issuer_name": "サンプルソリューション株式会社", "issuer_address": "〒105-0001 東京都港区1-2-3",
                "issuer_contact": "経理部　03-0000-0000",
            },
            "summary": {
                "primary_label": profile["primary_label"], "primary": "418,000円",
                "secondary_label": profile["secondary_label"], "secondary": "2026年10月31日",
                "tertiary_label": profile["tertiary_label"], "tertiary": "T1234567890123",
            },
            "items": [
                item(1, "SET-001", "業務システム初期設定", "1", "式", "300,000円 / 10%", "300,000円"),
                item(2, "TRN-002", "操作研修（オンライン）", "2", "回", "50,000円 / 10%", "100,000円"),
            ],
            "terms": {"label": profile["terms_label"], "body": "振込手数料はご負担ください。\n登録番号：T1234567890123"},
            "totals": {"rows": [
                {"label": "税抜小計", "value": "400,000円"}, {"label": "値引額", "value": "▲20,000円"},
                {"label": "消費税額", "value": "38,000円"}, {"label": "請求合計", "value": "418,000円"},
            ]},
        })
    elif kind == "delivery_note":
        number = "DN-2026-0176"
        document.update({
            "number": number, "date": "2026年9月20日", "related_number": "PO-2026-0042",
            "readable_id": number, "barcode": barcode(number),
        })
        common.update({
            "party": {
                "recipient_label": "納入先", "recipient_name": "東都物流センター 御中",
                "recipient_address": "〒135-0001\n東京都江東区1-4-8", "issuer_label": "納品者",
                "issuer_name": "サンプルソリューション株式会社", "issuer_address": "〒105-0001 東京都港区1-2-3",
                "issuer_contact": "出荷担当　03-0000-0000",
            },
            "summary": {
                "primary_label": profile["primary_label"], "primary": "8箱 / 24点",
                "secondary_label": profile["secondary_label"], "secondary": "2026年9月20日",
                "tertiary_label": profile["tertiary_label"], "tertiary": "PO-2026-0042",
            },
            "items": [
                item(1, "MON-101", "24インチモニター", "4", "台", "LOT-M2409", "受領 ○"),
                item(2, "ARM-204", "モニターアーム", "4", "台", "LOT-A2409", "受領 ○"),
                item(3, "CAB-010", "接続ケーブル一式", "2", "箱", "LOT-C2409", "受領 ○"),
            ],
            "terms": {"label": profile["terms_label"], "body": "納品時の外観確認済み。\n不足・破損がある場合はこの欄へ記入してください。"},
            "totals": {"rows": [
                {"label": "納品数量", "value": "8箱 / 24点"}, {"label": "受領済", "value": "8箱 / 24点"},
                {"label": "不足・破損", "value": "なし"}, {"label": "受領確認", "value": "担当者記入"},
            ]},
        })
    else:
        raise ValueError(f"unknown document kind: {kind}")
    return common


def render_all() -> tuple[Path, ...]:
    """4種類を同じテンプレートから生成して、生成先を返す。"""
    outputs: list[Path] = []
    for kind in DOCUMENT_PROFILES:
        output_path = OUTPUT_DIR / OUTPUT_NAMES[kind]
        output_path.write_text(svg_report_template.render(document_data(kind)), encoding="utf-8")
        outputs.append(output_path)
    return tuple(outputs)


if __name__ == "__main__":
    for path in render_all():
        print(path)
