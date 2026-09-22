"""大きな和文見出し・縦書き・回転ラベルを持つポスター。"""

from pathlib import Path

from svgreportbuilder import SvgReportTemplate, TextField

TEXT = {
    "font-family": '"Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif',
    "font-size": "17px", "line-height": "1.8", "color": "#202b36",
    "white-space": "pre-wrap", "overflow-wrap": "anywhere",
}

svg_report_template = SvgReportTemplate(
    svg=Path(__file__).with_name("template.svg").read_text(encoding="utf-8"),
    fields=[
        TextField(
            target_id="title_box", value_path="title",
            container_style=TEXT | {"font-size": "96px", "font-weight": "900", "line-height": "1.13", "letter-spacing": "-4px"},
        ),
        TextField(
            target_id="edition_box", value_path="edition",
            container_style=TEXT | {"font-size": "15px", "font-weight": "700", "letter-spacing": "2px"},
        ),
        TextField(
            target_id="dates_box", value_path="dates",
            container_style=TEXT | {"font-size": "58px", "font-weight": "700", "line-height": "1.1", "letter-spacing": "-2px", "font-variant-numeric": "tabular-nums"},
        ),
        TextField(
            target_id="vertical_copy_box", value_path="vertical_copy",
            container_style=TEXT | {
                "writing-mode": "vertical-rl", "text-orientation": "mixed",
                "font-size": "23px", "line-height": "1.7", "letter-spacing": "5px",
            },
        ),
        TextField(
            target_id="badge_box", value_path="badge.label", target_fill_path="badge.fill",
            container_style=TEXT | {
                "display": "flex", "align-items": "center", "justify-content": "center",
                "text-align": "center", "font-size": "20px", "font-weight": "700", "line-height": "1.4",
            },
        ),
        TextField(target_id="description_box", value_path="description", container_style=TEXT),
        TextField(
            target_id="venue_box", value_path="venue",
            container_style=TEXT | {"font-size": "15px", "line-height": "1.85"},
        ),
        TextField(
            target_id="footer_box", value_path="footer",
            container_style=TEXT | {"font-size": "12px", "letter-spacing": "1px"},
        ),
    ],
)
