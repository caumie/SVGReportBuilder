"""領収書のサンプルデータを生成して SVG を出力する。"""

from __future__ import annotations

from pathlib import Path

from svgreportbuilder import Data, ImageSource

from .template_spec import svg_report_template


OUTPUT_PATH = Path(__file__).with_name("output-receipt.svg")


DATA: Data = {
    "document": {
        "copy_label": "原本",
        "number": "RCPT-2026-091",
        "date": "2026年9月20日",
        "reference_number": "INV-2026-0091",
        "barcode": None,
        "readable_id": "RCPT-2026-091",
    },
    "page": {"current": 1, "total": 1},
    "recipient": {"name": "株式会社みらい産業 御中"},
    "receipt": {
        "amount": "¥418,000",
        "purpose": "業務システム初期設定および操作研修費として",
        "payment_method": "銀行振込",
        "tax_amount": "¥38,000（10%）",
    },
    "issuer": {
        # PNGのバイト列を渡すと、出力SVGにbase64のData URIとして埋め込まれる。
        "logo": ImageSource(
            data=Path(__file__).parent.joinpath("sample-logo.png").read_bytes(),
            mime_type="image/png",
        ),
        "name": "サンプルソリューション株式会社",
        "address": "〒105-0001\n東京都港区1-2-3",
        "contact": "経理部　03-0000-0000",
        "registration_number": "T1234567890123",
    },
}


def render() -> Path:
    OUTPUT_PATH.write_text(svg_report_template.render(DATA), encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    print(render())
