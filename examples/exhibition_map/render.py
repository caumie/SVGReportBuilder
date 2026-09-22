"""同じ会場に昼・夕方の案内データを差し込み、静的なSVGを生成する。"""

from pathlib import Path

from svgreportbuilder import Data, DataValue

from .template_spec import svg_report_template


def rooms(*, evening: bool) -> list[DataValue]:
    """位置はテンプレートに固定し、展示情報・混雑表示だけを更新する。"""
    return [
        {
            "name": "素材の図書室",
            "description": "木、紙、土。手に取って、つくり手が選んだ素材の物語にふれる展示。",
            "status": {"label": "ゆったり", "fill": "#dcebdc"},
        },
        {
            "name": "音をあつめる庭",
            "description": "まちの音を重ねて、自分だけの風景をつくる。ヘッドホンで楽しむ体験展示。",
            "status": {"label": "ゆったり" if evening else "約10分待ち", "fill": "#dcebdc" if evening else "#f5dfaf"},
        },
        {
            "name": "ひかりの実験室",
            "description": "透明な素材と影がつくる、小さな建築。時間とともに変わる色を探そう。",
            "status": {"label": "約15分待ち" if evening else "ゆったり", "fill": "#f5dfaf" if evening else "#dcebdc"},
        },
        {
            "name": "みんなのアトリエ",
            "description": "端材から小さなモビールをつくるワークショップ。道具は会場で貸し出します。",
            "status": {"label": "受付終了" if evening else "参加受付中", "fill": "#e4e6e0" if evening else "#dcebdc"},
        },
    ]


COMMON: Data = {
    "heading": "つくる人に、会いにいこう。",
    "subtitle": "2026.10.24 SAT　10:00–19:00 ／ 港のスタジオ　秋のオープンデー",
    "visitor_note": "気になる部屋から、自由にどうぞ。写真撮影は、各展示の案内をご確認ください。",
}

SCENARIOS: dict[str, Data] = {
    "output-exhibition-map.svg": {
        **COMMON,
        "rooms": rooms(evening=False),
        "talk": {"time": "14:30", "title": "素材からはじまる、\n新しいものづくり。", "description": "会場中央のラウンジにて。\n3組のつくり手による、制作の裏側をめぐる40分のトーク。予約不要。"},
        "snapshot": "昼の案内 / 13:00 時点のサンプルデータ · 混雑状況は生成時点の情報です。",
    },
    "output-exhibition-map-evening.svg": {
        **COMMON,
        "rooms": rooms(evening=True),
        "talk": {"time": "17:30", "title": "夜のアトリエで、\nデザインのつづき。", "description": "会場中央のラウンジにて。\n展示をめぐったあとは、つくり手と語り合うクロージングトークへ。"},
        "snapshot": "夕方の案内 / 17:00 時点のサンプルデータ · 混雑状況は生成時点の情報です。",
    },
}


if __name__ == "__main__":
    for filename, data in SCENARIOS.items():
        output_path = Path(__file__).with_name(filename)
        output_path.write_text(svg_report_template.render(data), encoding="utf-8")
        print(output_path)
