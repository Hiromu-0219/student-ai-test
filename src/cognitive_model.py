from __future__ import annotations

import hashlib
import math
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
    """Legacy cognitive model used before the BKT/IRT-inspired redesign."""

    model_name = "legacy"

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
            question,
        )
        roll = _deterministic_roll(question["question_id"])
        target_correct = roll < probability
        expected_value = extract_x_value(question["answer"])
        target_value = expected_value if target_correct else _wrong_value(expected_value, question["skill"])

        return {
            "mode": "assessment",
            "cognitive_model": self.model_name,
            "target_correct": target_correct,
            "correct_probability": probability,
            "roll": roll,
            "skill": skill,
            "skill_score": skill_score,
            "overall_score": overall_score,
            "problem_difficulty": question.get("difficulty"),
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
        question: dict[str, Any] | None = None,
    ) -> int:
        probability = round(skill_score * 0.75 + overall_score * 0.25)
        probability += LEVEL_ADJUSTMENT.get(student_state.get("self_efficacy", "medium"), 0)
        probability += round(LEVEL_ADJUSTMENT.get(student_state.get("motivation", "medium"), 0) / 2)
        probability -= misconception_penalty
        return max(5, min(95, probability))

    def _rationale(self, target_correct: bool, skill: str, skill_score: int) -> str:
        if target_correct:
            return f"{skill} score is {skill_score}, so this item is set to correct."
        return f"{skill} score is {skill_score}, so this item is set to incorrect."


class BKTIRTCognitiveModel(CognitiveModel):
    """BKT/IRT-inspired interpretable cognitive model.

    This is not a fitted statistical BKT/IRT model. It is a controllable
    approximation for simulation: skill mastery is latent, correctness is
    observed, item difficulty matters, and guess/slip prevent deterministic
    behavior.
    """

    model_name = "bkt_irt"

    def build_assessment_directive(
        self,
        *,
        student_state: dict[str, Any],
        question: dict[str, Any],
    ) -> dict[str, Any]:
        directive = super().build_assessment_directive(
            student_state=student_state,
            question=question,
        )
        skill_score = directive["skill_score"]
        overall_score = directive["overall_score"]
        difficulty_score = _difficulty_score(question.get("difficulty", 1))
        ability = _ability_score(skill_score, overall_score)
        guess = _guess_probability(difficulty_score)
        slip = _slip_probability(
            difficulty_score,
            student_state.get("self_efficacy", "medium"),
            student_state.get("motivation", "medium"),
        )
        directive.update(
            {
                "difficulty_score": difficulty_score,
                "ability_skill_match": round(ability - difficulty_score, 1),
                "guess_probability": guess,
                "slip_probability": slip,
            }
        )
        return directive

    def _correct_probability(
        self,
        student_state: dict[str, Any],
        skill_score: int,
        overall_score: int,
        misconception_penalty: int,
        question: dict[str, Any] | None = None,
    ) -> int:
        question = question or {}
        difficulty_score = _difficulty_score(question.get("difficulty", 1))
        ability = _ability_score(skill_score, overall_score)
        guess = _guess_probability(difficulty_score)
        slip = _slip_probability(
            difficulty_score,
            student_state.get("self_efficacy", "medium"),
            student_state.get("motivation", "medium"),
        )

        mastery = max(0.0, min(1.0, ability / 100))
        bkt_probability = mastery * (100 - slip) + (1 - mastery) * guess

        irt_curve = 1 / (1 + math.exp(-((ability - difficulty_score) / 12)))
        irt_probability = guess + (100 - guess - slip) * irt_curve

        probability = round((bkt_probability * 0.45) + (irt_probability * 0.55))
        probability += round(LEVEL_ADJUSTMENT.get(student_state.get("self_efficacy", "medium"), 0) / 2)
        probability += round(LEVEL_ADJUSTMENT.get(student_state.get("motivation", "medium"), 0) / 3)
        probability -= misconception_penalty
        return max(5, min(95, probability))


def create_cognitive_model(model_type: str = "legacy") -> CognitiveModel:
    normalized = model_type.strip().lower().replace("-", "_")
    if normalized in {"legacy", "standard", "cognitive"}:
        return CognitiveModel()
    if normalized in {"bkt_irt", "bktirt", "bkt", "irt"}:
        return BKTIRTCognitiveModel()
    raise ValueError(f"Unknown cognitive model type: {model_type}")


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
        "can_transpose_terms": ["移項", "符号", "反対側", "遘", "隨", "蜿"],
        "can_divide_by_coefficient": ["係数", "割", "引", "3x", "菫", "蜑", "蠑"],
        "can_handle_negative_numbers": ["マイナス", "負", "-", "繝槭う繝翫せ", "雋"],
        "can_handle_fractions": ["分数", "分母", "/", "蛻"],
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
        "weak": 0.12,
        "medium": 0.25,
        "strong": 0.40,
    }[strength]
    return max(0, round((100 - effective_score) * multiplier))


def _difficulty_score(raw_difficulty: Any) -> int:
    if isinstance(raw_difficulty, (int, float)):
        difficulty = float(raw_difficulty)
    else:
        difficulty = 1.0
    if difficulty <= 5:
        return max(10, min(95, round(15 + difficulty * 15)))
    return max(0, min(100, round(difficulty)))


def _ability_score(skill_score: int, overall_score: int) -> float:
    return skill_score * 0.85 + overall_score * 0.15


def _guess_probability(difficulty_score: int) -> int:
    return max(5, min(20, round(22 - difficulty_score * 0.18)))


def _slip_probability(difficulty_score: int, self_efficacy: str, motivation: str) -> int:
    slip = 4 + round(difficulty_score * 0.08)
    if self_efficacy in {"very_low", "low"}:
        slip += 3
    elif self_efficacy in {"high", "very_high"}:
        slip -= 1
    if motivation in {"very_low", "low"}:
        slip += 2
    elif motivation in {"high", "very_high"}:
        slip -= 1
    return max(3, min(25, slip))
