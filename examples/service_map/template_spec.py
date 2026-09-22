"""SVGの接続図と、説明・状態・数値を組版するHTMLカード。"""

from pathlib import Path

from svgreportbuilder import FixedSlots, SvgReportTemplate, TextField

TEXT = {
    "font-family": '"Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif',
    "font-size": "14px", "line-height": "1.6", "color": "#b4c5d0",
    "overflow-wrap": "anywhere",
}
BADGE = TEXT | {
    "display": "flex", "align-items": "center", "justify-content": "center",
    "font-size": "12px", "font-weight": "700", "line-height": "1", "color": "#172d30",
}

svg_report_template = SvgReportTemplate(
    svg=Path(__file__).with_name("template.svg").read_text(encoding="utf-8"),
    fields=[
        TextField(
            target_id="heading_box", value_path="heading",
            container_style=TEXT | {"font-size": "40px", "font-weight": "700", "line-height": "1.3", "color": "#edf3f6"},
        ),
        TextField(target_id="subtitle_box", value_path="subtitle", container_style=TEXT),
        TextField(
            target_id="overall_box", value_path="overall.label", target_fill_path="overall.fill",
            container_style=BADGE | {"font-size": "15px"},
        ),
        FixedSlots(
            value_path="nodes", capacity=4, min_items=4, index="node",
            fields=[
                # カード全体のrectへ種別を置き、同時に状態由来の枠色を適用。
                TextField(
                    target_id="node_{node}_panel_box", value_path="kind",
                    target_fill_path="appearance.fill", target_stroke_path="appearance.stroke",
                    container_style=TEXT | {"padding": "18px 20px", "font-size": "11px", "letter-spacing": "1px"},
                ),
                TextField(
                    target_id="node_{node}_name_box", value_path="name",
                    container_style=TEXT | {"font-size": "23px", "font-weight": "700", "line-height": "1.3", "color": "#edf3f6"},
                ),
                TextField(
                    target_id="node_{node}_description_box", value_path="description",
                    container_style=TEXT | {"font-size": "13px"},
                ),
                TextField(
                    target_id="node_{node}_metric_box", value_path="metric",
                    container_style=TEXT | {"font-family": '"Noto Sans Mono CJK JP", monospace', "font-size": "13px", "font-variant-numeric": "tabular-nums", "color": "#edf3f6"},
                ),
                TextField(
                    target_id="node_{node}_status_box", value_path="status.label",
                    target_fill_path="status.fill", container_style=BADGE,
                ),
            ],
        ),
        TextField(
            target_id="summary_box", value_path="summary",
            container_style=TEXT | {"display": "flex", "align-items": "center", "font-size": "13px"},
        ),
    ],
)
