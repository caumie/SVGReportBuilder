"""会場の幾何形状に、HTMLの折り返しと中央揃えを重ねる。"""

from pathlib import Path

from svgreportbuilder import FixedSlots, SvgReportTemplate, TextField

TEXT = {
    "font-family": '"Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif',
    "font-size": "15px",
    "line-height": "1.65",
    "color": "#243d32",
    "overflow-wrap": "anywhere",
}

svg_report_template = SvgReportTemplate(
    svg=Path(__file__).with_name("template.svg").read_text(encoding="utf-8"),
    fields=[
        TextField(
            target_id="heading_box", value_path="heading",
            container_style=TEXT | {"font-size": "42px", "font-weight": "700", "line-height": "1.3"},
        ),
        TextField(target_id="subtitle_box", value_path="subtitle", container_style=TEXT),
        FixedSlots(
            value_path="rooms", capacity=4, min_items=4, index="room",
            fields=[
                TextField(
                    target_id="room_{room}_name_box", value_path="name",
                    container_style=TEXT | {"font-size": "22px", "font-weight": "700", "line-height": "1.4"},
                ),
                TextField(
                    target_id="room_{room}_description_box", value_path="description",
                    container_style=TEXT | {"font-size": "14px", "line-height": "1.5"},
                ),
                TextField(
                    target_id="room_{room}_status_box", value_path="status.label",
                    target_fill_path="status.fill",
                    container_style=TEXT | {
                        "display": "flex", "align-items": "center", "justify-content": "center",
                        "font-size": "12px", "font-weight": "700", "line-height": "1",
                    },
                ),
            ],
        ),
        TextField(
            target_id="talk_time_box", value_path="talk.time",
            container_style=TEXT | {
                "font-size": "48px", "font-weight": "700", "line-height": "1.2",
                "font-variant-numeric": "tabular-nums", "color": "#f3e8a5",
            },
        ),
        TextField(
            target_id="talk_title_box", value_path="talk.title",
            container_style=TEXT | {"font-size": "26px", "font-weight": "700", "line-height": "1.45", "color": "#fffef9"},
        ),
        TextField(
            target_id="talk_description_box", value_path="talk.description",
            container_style=TEXT | {"font-size": "14px", "color": "#d7e3d5"},
        ),
        TextField(target_id="visitor_note_box", value_path="visitor_note", container_style=TEXT),
        TextField(
            target_id="snapshot_box", value_path="snapshot",
            container_style=TEXT | {"font-size": "11px", "color": "#607364"},
        ),
    ],
)
