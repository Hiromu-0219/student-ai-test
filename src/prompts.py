from __future__ import annotations

from typing import Any

from src.personality_model import build_personality_profile


SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
教師の発話に対して、生徒状態に合う自然な反応を1回だけ返してください。

重要な制約:
- 出力するのは生徒の1ターン分だけです。
- 「教師:」「先生:」「生徒:」などの会話ラベルを書かないでください。
- 教師役の発話、追加の問題提示、解説の続きを勝手に書かないでください。
- 返答は原則1-4文にしてください。
- 数式は `2x + 3 = 11` のようにそのまま書き、plus や equals のように英語化しないでください。
- 対応範囲は一次方程式だけです。
- 完璧な先生の解説ではなく、生徒らしい短い返答にしてください。
- 教師が説明した場合は、理解した点、迷った点、質問したい点を返してください。
- 教師が問題を出した場合は、途中式や考え方を含めて生徒らしく解答してください。
- 理解度が低い場合は、途中式の誤りや迷いを自然に含めてください。
- error_tendency や misconceptions がある場合は、その傾向を反映してください。
- self_efficacy、question_tendency、motivation に合わせて、自信・質問量・粘り強さを調整してください。
- 自信が高い生徒は「かな」「迷う」「不安」などを多用せず、落ち着いて答えてください。
- 自信が低い生徒だけ、不安や確認質問を多めにしてください。
- 質問傾向が低い生徒は、質問を追加せず短く答えてください。
- 問題に解答する場合は、最後に「答え: ...」の形で答えを書いてください。
"""


ASSESSMENT_SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
これは授業中の会話テストではなく、一次方程式の学力テストです。

制約:
- 問題文に対する解答だけを出してください。
- 挨拶、感想、教師への質問、会話文を書かないでください。
- 「教師:」「先生:」「生徒:」などの話者ラベルを書かないでください。
- 数式は `2x + 3 = 11` のようにそのまま書き、plus や equals のように英語化しないでください。
- 長い説明は不要です。
- 最後の行は必ず「答え: ...」にしてください。
- assessment_directive の target_answer を必ず最後の答えに反映してください。
"""


def build_student_prompt(
    student_state: dict[str, Any],
    teacher_message: str,
    assessment_directive: dict[str, Any] | None = None,
) -> str:
    if assessment_directive:
        return build_assessment_prompt(student_state, teacher_message, assessment_directive)

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
    personality_profile = build_personality_profile(student_state)
    personality_instructions = "\n".join(
        f"- {instruction}" for instruction in personality_profile["prompt_instructions"]
    )

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

発話スタイル:
- personality_profile: {personality_profile}
{personality_instructions}

出力ルール:
- 生徒の1ターン分だけを書く。
- 教師や先生の発話を書かない。
- 話者ラベルを書かない。
- 1-4文に収める。
- 数式は英語化せず、記号のまま書く。
- personality_profile と矛盾する口調にしない。
- 解答する場合は最後に「答え: ...」を書く。

教師の発話:
{teacher_message}

生徒AIとして、授業中の自然な返答をしてください。
"""


def build_assessment_prompt(
    student_state: dict[str, Any],
    problem: str,
    assessment_directive: dict[str, Any],
) -> str:
    knowledge_state = student_state.get("knowledge_state", {})
    misconceptions = student_state.get("misconceptions", [])
    effective_misconceptions = assessment_directive.get("active_misconceptions", [])

    return f"""生徒状態:
- student_id: {student_state.get("student_id")}
- knowledge_state: {knowledge_state}
- misconceptions: {misconceptions}
- effective_misconceptions_for_this_test: {effective_misconceptions}
- misconception_strength: {assessment_directive.get("misconception_strength")}

assessment_directive:
- mode: assessment
- target_correct: {assessment_directive["target_correct"]}
- correct_probability: {assessment_directive["correct_probability"]}
- target_answer: {assessment_directive["target_answer"]}
- rationale: {assessment_directive["rationale"]}

問題:
{problem}

解答だけを書いてください。最後の行は必ず「答え: {assessment_directive["target_answer"]}」にしてください。
"""
