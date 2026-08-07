from __future__ import annotations

from typing import Any

from src.personality_model import build_personality_profile


SOLVE_PHASES = ("例題", "確認問題", "テスト", "問題")
PRACTICE_PHASES = ("個別演習", "演習")
LISTEN_PHASES = ("導入", "全体説明", "説明", "まとめ")


def build_student_behavior(
    student_state: dict[str, Any],
    teacher_message: str,
    assessment_directive: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decide what the student should do before natural-language generation.

    The behavior model controls simulation-critical actions. The LLM only
    verbalizes this directive.
    """

    phase_type = _phase_type(teacher_message, assessment_directive)
    profile = build_personality_profile(student_state)
    traits = _traits(student_state, profile)

    if assessment_directive:
        action_type = "solve"
        should_solve = True
        should_include_answer = True
    elif phase_type == "practice":
        action_type = "practice"
        should_solve = True
        should_include_answer = True
    elif phase_type == "solve":
        action_type = "solve"
        should_solve = True
        should_include_answer = True
    elif phase_type == "listen":
        action_type = "acknowledge"
        should_solve = False
        should_include_answer = False
    else:
        action_type = "respond"
        should_solve = False
        should_include_answer = False

    should_ask_question = _should_ask_question(action_type, traits, assessment_directive)
    should_show_work = _should_show_work(action_type, traits)
    should_express_uncertainty = _should_express_uncertainty(traits, assessment_directive)

    return {
        "phase_type": phase_type,
        "action_type": action_type,
        "should_solve": should_solve,
        "should_include_answer": should_include_answer,
        "should_ask_question": should_ask_question,
        "should_show_work": should_show_work,
        "should_express_uncertainty": should_express_uncertainty,
        "target_answer": (assessment_directive or {}).get("target_answer"),
        "target_correct": (assessment_directive or {}).get("target_correct"),
        "style": {
            "verbosity": profile.get("verbosity"),
            "step_detail": profile.get("step_detail"),
            "emotional_tone": profile.get("emotional_tone"),
            "question_behavior": profile.get("question_behavior"),
        },
        "constraints": _constraints(
            should_solve=should_solve,
            should_include_answer=should_include_answer,
            should_ask_question=should_ask_question,
            should_show_work=should_show_work,
        ),
    }


def fallback_utterance_for_behavior(behavior: dict[str, Any]) -> str:
    if behavior.get("should_solve"):
        target_answer = behavior.get("target_answer") or "x = わかりません"
        if behavior.get("should_express_uncertainty"):
            return f"少し迷いますが、計算してみます。答え: {target_answer}"
        return f"計算してみます。答え: {target_answer}"
    if behavior.get("should_ask_question"):
        return "はい、確認します。係数で割るところをもう少し意識します。"
    if behavior.get("should_express_uncertainty"):
        return "はい、少し不安ですが、今日の目標を確認します。"
    return "はい、今日の内容を確認します。"


def _phase_type(
    teacher_message: str,
    assessment_directive: dict[str, Any] | None,
) -> str:
    if assessment_directive:
        return "solve"
    text = str(teacher_message)
    if "今日の目標" in text or "全体説明" in text:
        return "listen"
    if any(token in text for token in PRACTICE_PHASES):
        return "practice"
    if any(token in text for token in SOLVE_PHASES):
        return "solve"
    if _contains_linear_equation(text):
        return "solve"
    if any(token in text for token in LISTEN_PHASES):
        return "listen"
    return "respond"


def _contains_linear_equation(text: str) -> bool:
    return bool(__import__("re").search(r"[+-]?\d*\s*x(?:\s*[+-]\s*\d+)?\s*=\s*[+-]?\d+", text.replace("　", " ")))


def _traits(student_state: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    return {
        "self_efficacy": str(student_state.get("self_efficacy", "medium")),
        "question_tendency": str(student_state.get("question_tendency", "medium")),
        "motivation": str(student_state.get("motivation", "medium")),
        "confidence_expression": str(profile.get("confidence_expression", "medium")),
        "question_behavior": str(profile.get("question_behavior", "neutral")),
        "emotional_tone": str(profile.get("emotional_tone", "neutral")),
        "step_detail": str(profile.get("step_detail", "medium")),
    }


def _should_ask_question(
    action_type: str,
    traits: dict[str, str],
    assessment_directive: dict[str, Any] | None,
) -> bool:
    if traits["question_tendency"] in {"high", "very_high"}:
        return action_type in {"acknowledge", "practice", "solve"}
    if assessment_directive and assessment_directive.get("target_correct") is False:
        return traits["question_tendency"] == "medium"
    return False


def _should_show_work(action_type: str, traits: dict[str, str]) -> bool:
    if action_type not in {"solve", "practice"}:
        return False
    return traits["step_detail"] in {"medium", "shows_steps"} or traits["motivation"] in {"high", "very_high"}


def _should_express_uncertainty(
    traits: dict[str, str],
    assessment_directive: dict[str, Any] | None,
) -> bool:
    if traits["self_efficacy"] in {"very_low", "low"}:
        return True
    if traits["emotional_tone"] == "anxious":
        return True
    return bool(assessment_directive and assessment_directive.get("target_correct") is False and traits["self_efficacy"] == "medium")


def _constraints(
    *,
    should_solve: bool,
    should_include_answer: bool,
    should_ask_question: bool,
    should_show_work: bool,
) -> list[str]:
    constraints = []
    if should_solve:
        constraints.append("問題を解く")
    else:
        constraints.append("問題を解かない")
    if should_include_answer:
        constraints.append("最後に答えを書く")
    else:
        constraints.append("答えを書かない")
    constraints.append("質問を入れてよい" if should_ask_question else "質問を追加しない")
    constraints.append("途中式を出してよい" if should_show_work else "途中式を出さない")
    return constraints



