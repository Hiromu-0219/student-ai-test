from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from src.grader import extract_x_value


LEVEL_ADJUSTMENT = {
    "very_low": -10,
    "low": -5,
    "medium": 0,
    "high": 5,
    "very_high": 10,
}


class CognitiveModel:
    def build_assessment_directive(
        self,
        *,
        student_state: dict[str, Any],
        question: dict[str, Any],
    ) -> dict[str, Any]:
        linear_state = student_state.get("knowledge_state", {}).get("linear_equation", {})
        skill = question["skill"]
        skill_score = _score(linear_state.get(skill, linear_state.get("score", 0)))
        overall_score = _score(linear_state.get("score", skill_score))
        related_misconceptions = _related_misconceptions(
            student_state.get("misconceptions", []),
            skill,
        )
        misconception_strength = _misconception_strength(
            skill_score,
            overall_score,
            bool(related_misconceptions),
        )
        misconception_penalty = _misconception_penalty(
            misconception_strength,
            skill_score,
            overall_score,
        )
        probability = self._correct_probability(
            student_state,
            skill_score,
            overall_score,
            misconception_penalty,
        )
        roll = _deterministic_roll(question["question_id"])
        target_correct = roll < probability
        expected_value = extract_x_value(question["answer"])
        target_value = expected_value if target_correct else _wrong_value(expected_value, question["skill"])

        return {
            "mode": "assessment",
            "target_correct": target_correct,
            "correct_probability": probability,
            "roll": roll,
            "skill": skill,
            "skill_score": skill_score,
            "overall_score": overall_score,
            "misconception_penalty": misconception_penalty,
            "misconception_strength": misconception_strength,
            "active_misconceptions": _active_misconceptions(
                related_misconceptions,
                misconception_strength,
            ),
            "expected_answer": question["answer"],
            "target_answer": f"x = {_format_fraction(target_value)}",
            "rationale": self._rationale(target_correct, skill, skill_score),
        }

    def _correct_probability(
        self,
        student_state: dict[str, Any],
        skill_score: int,
        overall_score: int,
        misconception_penalty: int,
    ) -> int:
        probability = round(skill_score * 0.75 + overall_score * 0.25)
        probability += LEVEL_ADJUSTMENT.get(student_state.get("self_efficacy", "medium"), 0)
        probability += round(LEVEL_ADJUSTMENT.get(student_state.get("motivation", "medium"), 0) / 2)
        probability -= misconception_penalty
        return max(5, min(95, probability))

    def _rationale(self, target_correct: bool, skill: str, skill_score: int) -> str:
        if target_correct:
            return f"{skill} のスコアが {skill_score} なので、この問題は正答できる想定。"
        return f"{skill} のスコアが {skill_score} なので、この問題では誤答する想定。"


def _score(value: Any) -> int:
    if isinstance(value, bool):
        return 100 if value else 0
    if isinstance(value, (int, float)):
        return max(0, min(100, int(round(value))))
    return 0


def _deterministic_roll(question_id: str) -> int:
    digest = hashlib.sha256(question_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _wrong_value(expected_value: Fraction | None, skill: str) -> Fraction:
    if expected_value is None:
        return Fraction(0)
    if skill == "can_transpose_terms":
        return expected_value - 1
    if skill == "can_divide_by_coefficient":
        return expected_value + 2
    if skill == "can_handle_negative_numbers":
        return -expected_value
    if skill == "can_handle_fractions":
        return expected_value / 2
    return expected_value + 1


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _related_misconceptions(misconceptions: list[str], skill: str) -> list[str]:
    keywords = {
        "can_transpose_terms": ["移項", "符号", "反対側"],
        "can_divide_by_coefficient": ["係数", "割", "引けば"],
        "can_handle_negative_numbers": ["マイナス", "負", "-"],
        "can_handle_fractions": ["分数", "/"],
    }.get(skill, [])
    return [
        misconception
        for misconception in misconceptions
        if any(keyword in misconception for keyword in keywords)
    ]


def _misconception_strength(skill_score: int, overall_score: int, has_related_misconception: bool) -> str:
    if not has_related_misconception:
        return "none"
    effective_score = max(skill_score, overall_score)
    if effective_score >= 90:
        return "none"
    if effective_score >= 70:
        return "weak"
    if effective_score >= 40:
        return "medium"
    return "strong"


def _active_misconceptions(misconceptions: list[str], strength: str) -> list[dict[str, str]]:
    if strength == "none":
        return []
    return [{"text": misconception, "strength": strength} for misconception in misconceptions]


def _misconception_penalty(strength: str, skill_score: int, overall_score: int) -> int:
    if strength == "none":
        return 0
    effective_score = max(skill_score, overall_score)
    multiplier = {
        "weak": 0.10,
        "medium": 0.18,
        "strong": 0.30,
    }[strength]
    return max(0, round((100 - effective_score) * multiplier))
