"""共通のアートワークから、異なる展覧会告知を生成する。"""

from pathlib import Path

from svgreportbuilder import Data

from .template_spec import svg_report_template

SCENARIOS: dict[str, Data] = {
    "output-event-poster.svg": {
        "title": "余白を、\nあそぶ。",
        "edition": "暮らしの実験展  vol. 01　/　2026",
        "dates": "10.24 — 11.08",
        "vertical_copy": "何もないところから、日常が動きだす。",
        "badge": {"label": "見て、さわって。\n入場無料", "fill": "#c5d277"},
        "description": "椅子ひとつ、紙一枚、光のひとすじ。\nいつもの道具と空間のあいだにある「余白」を、\n12組のつくり手と一緒に見つめ直す展覧会。",
        "venue": "港のギャラリー\n10:00–18:00\n最終日は17:00まで\n会期中無休",
        "footer": "主催：FORM / LIFE 実行委員会　　企画・会場はサンプルです。",
    },
    "output-event-poster-light.svg": {
        "title": "光と、\n暮らす。",
        "edition": "暮らしの実験展  vol. 02　/　2026",
        "dates": "12.05 — 12.20",
        "vertical_copy": "窓辺の小さな変化を、見つけにいこう。",
        "badge": {"label": "金曜は夜まで。\nNIGHT OPEN", "fill": "#f4d68b"},
        "description": "朝の窓辺、夕暮れのテーブル。\n暮らしの景色を変える光のかたちを、\n写真と道具とインスタレーションでたどります。",
        "venue": "港のギャラリー\n11:00–19:00\n金曜は21:00まで\n月曜休館",
        "footer": "主催：FORM / LIFE 実行委員会　　企画・会場はサンプルです。",
    },
}


if __name__ == "__main__":
    for filename, data in SCENARIOS.items():
        output_path = Path(__file__).with_name(filename)
        output_path.write_text(svg_report_template.render(data), encoding="utf-8")
        print(output_path)
