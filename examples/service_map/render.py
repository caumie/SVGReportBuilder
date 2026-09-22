"""正常時と遅延発生時のスナップショット。外部の監視サービスには接続しない。"""

from pathlib import Path

from svgreportbuilder import Data, DataValue

from .template_spec import svg_report_template


def node(kind: str, name: str, description: str, metric: str, *, delayed: bool = False) -> Data:
    return {
        "kind": kind, "name": name, "description": description, "metric": metric,
        "appearance": {"fill": "#34302c" if delayed else "#1c303e", "stroke": "#edb966" if delayed else "#456273"},
        "status": {"label": "遅延あり" if delayed else "正常", "fill": "#f4c783" if delayed else "#b9e5c5"},
    }


def nodes(*, incident: bool) -> list[DataValue]:
    return [
        node("01 / CLIENT", "Web client", "商品検索と注文画面を提供するフロントエンド。", "active users     1,284"),
        node("02 / API", "Order API", "注文を受け付け、在庫照会と非同期ジョブの登録を行う。", "p95 latency    1,240 ms" if incident else "p95 latency       84 ms", delayed=incident),
        node("03 / STORAGE", "Primary database", "注文データと在庫の永続化。読み取りレプリカへ変更を同期。", "connections      42 / 100"),
        node("04 / WORKER", "Fulfillment worker", "配送指示と通知をバックグラウンドで処理する。", "queue depth        382" if incident else "queue depth          3", delayed=incident),
    ]


COMMON: Data = {
    "heading": "サービスのつながりを、見える形に。",
    "subtitle": "ATLAS STORE　/　production · ap-northeast-1　/　構成と稼働状況のスナップショット",
}

SCENARIOS: dict[str, Data] = {
    "output-service-map.svg": {
        **COMMON, "nodes": nodes(incident=False),
        "overall": {"label": "すべて正常に稼働", "fill": "#b9e5c5"},
        "summary": "09:00 UTC / サンプルデータ　すべてのサービスが通常の範囲で動作しています。キューの滞留はありません。",
    },
    "output-service-map-incident.svg": {
        **COMMON, "nodes": nodes(incident=True),
        "overall": {"label": "一部に処理遅延", "fill": "#f4c783"},
        "summary": "09:15 UTC / サンプルデータ　注文集中により API 応答と配送処理が遅延。ワーカー増設後、キューの解消を確認中です。",
    },
}


if __name__ == "__main__":
    for filename, data in SCENARIOS.items():
        output_path = Path(__file__).with_name(filename)
        output_path.write_text(svg_report_template.render(data), encoding="utf-8")
        print(output_path)
