from __future__ import annotations

from typing import Any


LEVEL_ORDER = {
    "very_low": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "very_high": 4,
}


def build_personality_profile(student_state: dict[str, Any]) -> dict[str, Any]:
    big_five = student_state.get("big_five", {})
    self_efficacy = _level(student_state.get("self_efficacy", "medium"))
    question_tendency = _level(student_state.get("question_tendency", "medium"))
    motivation = _level(student_state.get("motivation", "medium"))
    conscientiousness = _level(big_five.get("conscientiousness", "medium"))
    extraversion = _level(big_five.get("extraversion", "medium"))
    agreeableness = _level(big_five.get("agreeableness", "medium"))
    neuroticism = _level(big_five.get("neuroticism", "medium"))
    openness = _level(big_five.get("openness", "medium"))

    profile = {
        "confidence_expression": _confidence_expression(self_efficacy, neuroticism),
        "question_behavior": _question_behavior(question_tendency, self_efficacy),
        "motivation_expression": _motivation_expression(motivation),
        "verbosity": _verbosity(extraversion, motivation),
        "step_detail": _step_detail(conscientiousness),
        "emotional_tone": _emotional_tone(neuroticism, self_efficacy),
        "teacher_alignment": _teacher_alignment(agreeableness),
        "strategy_flexibility": _strategy_flexibility(openness),
    }
    profile["prompt_instructions"] = _prompt_instructions(profile)
    return profile


def _level(value: Any) -> int:
    if isinstance(value, str):
        return LEVEL_ORDER.get(value, LEVEL_ORDER["medium"])
    if isinstance(value, (int, float)):
        return max(0, min(4, int(round(value))))
    return LEVEL_ORDER["medium"]


def _confidence_expression(self_efficacy: int, neuroticism: int) -> str:
    if self_efficacy <= 1 or neuroticism >= 4:
        return "low"
    if self_efficacy >= 3 and neuroticism <= 2:
        return "high"
    return "medium"


def _question_behavior(question_tendency: int, self_efficacy: int) -> str:
    if question_tendency >= 3:
        return "asks_specific_questions"
    if question_tendency <= 1 and self_efficacy <= 1:
        return "hides_confusion"
    if question_tendency <= 1:
        return "rarely_asks"
    return "asks_when_stuck"


def _motivation_expression(motivation: int) -> str:
    if motivation <= 1:
        return "gives_up_easily"
    if motivation >= 3:
        return "persists"
    return "neutral"


def _verbosity(extraversion: int, motivation: int) -> str:
    if extraversion <= 1 and motivation <= 2:
        return "short"
    if extraversion >= 3 or motivation >= 4:
        return "talkative"
    return "medium"


def _step_detail(conscientiousness: int) -> str:
    if conscientiousness <= 1:
        return "skips_steps"
    if conscientiousness >= 3:
        return "shows_steps"
    return "medium"


def _emotional_tone(neuroticism: int, self_efficacy: int) -> str:
    if neuroticism >= 3 and self_efficacy <= 2:
        return "anxious"
    if neuroticism <= 1 and self_efficacy >= 2:
        return "calm"
    return "neutral"


def _teacher_alignment(agreeableness: int) -> str:
    if agreeableness <= 1:
        return "reserved"
    if agreeableness >= 3:
        return "cooperative"
    return "neutral"


def _strategy_flexibility(openness: int) -> str:
    if openness <= 1:
        return "prefers_familiar_method"
    if openness >= 3:
        return "accepts_new_methods"
    return "neutral"


def _prompt_instructions(profile: dict[str, str]) -> list[str]:
    instructions = []
    if profile["confidence_expression"] == "low":
        instructions.append("自信なさげに、断定を避けて答える。")
    elif profile["confidence_expression"] == "high":
        instructions.append("自信を持って、はっきり答える。")
    else:
        instructions.append("自信は中程度で、必要に応じて確認する。")

    if profile["question_behavior"] == "asks_specific_questions":
        instructions.append("わからない点があれば具体的に質問する。")
    elif profile["question_behavior"] == "hides_confusion":
        instructions.append("わからなくても質問を控え、曖昧に返す。")
    elif profile["question_behavior"] == "rarely_asks":
        instructions.append("質問は少なめにする。")
    else:
        instructions.append("つまずいたときだけ短く質問する。")

    if profile["motivation_expression"] == "gives_up_easily":
        instructions.append("難しいと感じると粘りが弱くなる。")
    elif profile["motivation_expression"] == "persists":
        instructions.append("間違えてももう一度考えようとする。")

    if profile["verbosity"] == "short":
        instructions.append("返答を短めにする。")
    elif profile["verbosity"] == "talkative":
        instructions.append("考えたことをやや多めに話す。")

    if profile["step_detail"] == "skips_steps":
        instructions.append("途中式を省略しがちにする。")
    elif profile["step_detail"] == "shows_steps":
        instructions.append("途中式や手順を丁寧に出す。")

    if profile["emotional_tone"] == "anxious":
        instructions.append("不安や確認したい気持ちを少し出す。")
    elif profile["emotional_tone"] == "calm":
        instructions.append("落ち着いた口調にする。")

    if profile["teacher_alignment"] == "cooperative":
        instructions.append("教師の説明を素直に受け止める。")
    elif profile["teacher_alignment"] == "reserved":
        instructions.append("教師への反応を少しそっけなくする。")

    if profile["strategy_flexibility"] == "accepts_new_methods":
        instructions.append("別の解き方や説明を受け入れやすくする。")
    elif profile["strategy_flexibility"] == "prefers_familiar_method":
        instructions.append("慣れた解き方にこだわりやすくする。")

    return instructions
