from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
教師から出された一次方程式の問題に、生徒状態に合わせて回答してください。

制約:
- 対応範囲は一次方程式だけです。
- 完璧な先生の解説ではなく、生徒らしい短い回答にしてください。
- 生徒の理解度が低い場合は、途中式の誤りや迷いを自然に含めてください。
- error_tendency に該当するミスがあれば、その傾向を反映してください。
- misconceptions がある場合は、その誤概念に基づく考え方や誤答を自然に反映してください。
- self_efficacy、question_tendency、motivation に合わせて、自信・質問・粘り強さを調整してください。
- 最後に「答え: ...」の形で生徒の答えを書いてください。
"""


def build_student_prompt(student_state: dict[str, Any], problem: str) -> str:
    understanding = student_state.get("understanding", {})
    knowledge_state = student_state.get("knowledge_state", {})
    error_tendency = student_state.get("error_tendency", [])
    misconceptions = student_state.get("misconceptions", [])
    learning_speed = student_state.get("learning_speed", "normal")
    personality = student_state.get("personality", {})
    big_five = student_state.get("big_five", {})
    self_efficacy = student_state.get("self_efficacy", "medium")
    question_tendency = student_state.get("question_tendency", "medium")
    motivation = student_state.get("motivation", "medium")
    recent_history = student_state.get("learning_history", [])[-3:]

    return f"""生徒状態:
- student_id: {student_state.get("student_id")}
- name: {student_state.get("name")}
- understanding: {understanding}
- knowledge_state: {knowledge_state}
- error_tendency: {error_tendency}
- misconceptions: {misconceptions}
- learning_speed: {learning_speed}
- personality: {personality}
- big_five: {big_five}
- self_efficacy: {self_efficacy}
- question_tendency: {question_tendency}
- motivation: {motivation}
- recent_learning_history: {recent_history}

問題:
{problem}

生徒AIとして回答してください。
"""
