"""作業指示書のサンプルデータを生成して SVG を出力する。"""

from __future__ import annotations

from pathlib import Path

from svgreportbuilder import Data

from .template_spec import svg_report_template


OUTPUT_PATH = Path(__file__).with_name("output-work-order.svg")


DATA: Data = {
    "document": {
        "copy_label": "現場用",
        "number": "WO-2026-034",
        "date": "2026年9月20日",
        "reference_number": "JOB-42",
        "barcode": None,
        "readable_id": "WO-2026-034",
    },
    "page": {"current": 1, "total": 1},
    "job": {
        "name": "第2ライン 制御盤センサー更新",
        "quantity": "1 式",
        "planned_start": "2026年9月21日 09:00",
        "planned_end": "2026年9月21日 17:00",
        "equipment": "第2ライン / 制御盤 CP-02",
        "lot": "L2609-02",
        "preconditions": "停電許可を取得し、試運転前に安全柵の立会いを完了する。",
        "handover_reference": "INSP-2026-091（始業点検）",
        "instructed_by": "設備課長 田中",
        "supervisor": "現場責任者 佐藤",
    },
    "steps": [
        {
            "number": 1,
            "operation": "停電・ロックアウト",
            "criteria": "無電圧を検電で確認",
            "started_at": "09:00",
            "finished_at": "09:20",
            "operator": "佐藤",
            "checked_by": "田中",
        },
        {
            "number": 2,
            "operation": "既設センサー取り外し",
            "criteria": "端子番号を記録",
            "started_at": "09:25",
            "finished_at": "10:10",
            "operator": "佐藤",
            "checked_by": "",
        },
        {
            "number": 3,
            "operation": "新センサー取付・配線",
            "criteria": "配線表と照合",
            "started_at": "10:20",
            "finished_at": "13:40",
            "operator": "鈴木",
            "checked_by": "田中",
        },
        {
            "number": 4,
            "operation": "導通・絶縁測定",
            "criteria": "絶縁抵抗 1 MΩ以上",
            "started_at": "14:00",
            "finished_at": "15:10",
            "operator": "鈴木",
            "checked_by": "田中",
        },
        {
            "number": 5,
            "operation": "復電・試運転",
            "criteria": "警報なしで連続10分運転",
            "started_at": "15:30",
            "finished_at": "16:30",
            "operator": "佐藤",
            "checked_by": "主任 鈴木",
        },
    ],
}


def render() -> Path:
    OUTPUT_PATH.write_text(svg_report_template.render(DATA), encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    print(render())
