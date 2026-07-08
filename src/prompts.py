from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
教師から出された一次方程式の問題に、生徒状態に合わせて回答してください。

制約:
- 対応範囲は一次方程式だけです。
- 完璧な先生の解説ではなく、生徒らしい短い回答にしてください。
- 生徒の理解度が低い場合は、途中式の誤りや迷いを自然に含めてください。
- error_tendency に該当するミスがあれば、その傾向を反映してください。
- 最後に「答え: ...」の形で生徒の答えを書いてください。
"""


def build_student_prompt(student_state: dict[str, Any], problem: str) -> str:
    understanding = student_state.get("understanding", {})
    error_tendency = student_state.get("error_tendency", [])
    personality = student_state.get("personality", {})
    recent_history = student_state.get("learning_history", [])[-3:]

    return f"""生徒状態:
- student_id: {student_state.get("student_id")}
- name: {student_state.get("name")}
- understanding: {understanding}
- error_tendency: {error_tendency}
- personality: {personality}
- recent_learning_history: {recent_history}

問題:
{problem}

生徒AIとして回答してください。
"""
