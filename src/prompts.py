from __future__ import annotations

from typing import Any

from src.personality_model import build_personality_profile


SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
教師の発話に、生徒状態に合わせて回答してください。

制約:
- 対応範囲は一次方程式だけです。
- 完璧な先生の解説ではなく、生徒らしい短い回答にしてください。
- 教師が説明した場合は、理解したか、どこで迷ったか、質問したいことを生徒らしく返してください。
- 教師が問題を出した場合は、途中式や考え方を含めて生徒らしく解答してください。
- 生徒の理解度が低い場合は、途中式の誤りや迷いを自然に含めてください。
- error_tendency に該当するミスがあれば、その傾向を反映してください。
- misconceptions がある場合は、その誤概念に基づく考え方や誤答を自然に反映してください。
- self_efficacy、question_tendency、motivation に合わせて、自信・質問・粘り強さを調整してください。
- 問題に解答する場合は、最後に「答え: ...」の形で生徒の答えを書いてください。
- assessment_directive がある場合は、必ずその target_answer を最後の「答え: ...」に反映してください。
"""


ASSESSMENT_SYSTEM_PROMPT = """あなたは教育シミュレーション用の「生徒AI」です。
これは授業中の発話テストではなく、一次方程式の学力テストです。

制約:
- 問題文に対する解答だけを出してください。
- 挨拶、感想、教師への質問、会話文は書かないでください。
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
    directive_text = _format_assessment_directive(assessment_directive)
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

{directive_text}

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
- 理由: {assessment_directive["rationale"]}

問題:
{problem}

解答だけを書いてください。最後の行は必ず「答え: {assessment_directive["target_answer"]}」にしてください。
"""


def _format_assessment_directive(assessment_directive: dict[str, Any] | None) -> str:
    if not assessment_directive:
        return "assessment_directive: なし"
    target_answer = assessment_directive["target_answer"]
    correctness = "正答" if assessment_directive["target_correct"] else "誤答"
    return f"""assessment_directive:
- mode: assessment
- 方針: この問題では {correctness} する生徒として振る舞う。
- 理由: {assessment_directive["rationale"]}
- target_answer: {target_answer}
- 重要: 最後の行は必ず「答え: {target_answer}」にしてください。"""
