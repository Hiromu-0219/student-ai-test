from __future__ import annotations

import json
from typing import Any


TEACHER_SYSTEM_PROMPT = """あなたは教育シミュレーションの教師AIです。
生徒の状態、直近の発話、伝達AIの観察結果、単元目標を見て、次の授業手法を1つ以上選びます。
数学の正答だけでなく、生徒の理解度、誤概念、自己効力感、質問傾向、動機づけを考慮してください。
出力はJSONのみで返してください。"""


def build_teacher_strategy_prompt(context: dict[str, Any]) -> str:
    """Builds a future LLM prompt from the same context used by the rule selector."""

    return f"""次の情報から、教師AIの次の対応を決めてください。

必ず次のJSON形式で返してください。
{{
  "diagnosis": "生徒状態の短い診断",
  "selected_strategies": ["strategy_id"],
  "teacher_utterance": "教師として次に言う短い発話",
  "next_problem": "次に出す問題",
  "expected_answer": "期待される答え",
  "reason": "なぜその対応にしたか"
}}

入力コンテキスト:
{json.dumps(context, ensure_ascii=False, indent=2)}
"""
