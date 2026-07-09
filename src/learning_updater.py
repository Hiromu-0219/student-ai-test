from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


SKILL_KEYS = {
    "can_solve_ax_plus_b_equals_c",
    "can_transpose_terms",
    "can_divide_by_coefficient",
    "can_handle_negative_numbers",
    "can_handle_fractions",
}

LEARNING_SPEED_MULTIPLIER = {
    "very_low": 0.25,
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
    "very_high": 2.0,
}


class LearningUpdater:
    def update_after_interaction(
        self,
        student_state: dict[str, Any],
        *,
        teacher_message: str,
        student_answer: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        updated = deepcopy(student_state)
        linear_state = updated.setdefault("knowledge_state", {}).setdefault("linear_equation", {})
        self._ensure_numeric_knowledge_state(linear_state)

        base_delta = self._base_delta(teacher_message, student_answer)
        multiplier = LEARNING_SPEED_MULTIPLIER.get(updated.get("learning_speed", "medium"), 1.0)
        delta = max(0, min(8, round(base_delta * multiplier)))

        touched_skills = self._touched_skills(teacher_message)
        if delta > 0:
            linear_state["score"] = _clamp_score(linear_state.get("score", 0) + delta)
            for skill in touched_skills:
                linear_state[skill] = _clamp_score(linear_state.get(skill, 0) + delta)
            linear_state["level"] = _score_to_level(linear_state["score"])

        event = {
            "knowledge_delta": delta,
            "updated_score": linear_state.get("score", 0),
            "updated_level": linear_state.get("level", "very_low"),
            "touched_skills": sorted(touched_skills),
        }
        return updated, event

    def _ensure_numeric_knowledge_state(self, linear_state: dict[str, Any]) -> None:
        linear_state["score"] = _coerce_score(linear_state.get("score", linear_state.get("level", 0)))
        linear_state["level"] = _score_to_level(linear_state["score"])
        for skill in SKILL_KEYS:
            linear_state[skill] = _coerce_score(linear_state.get(skill, 0))

    def _base_delta(self, teacher_message: str, student_answer: str) -> int:
        text = f"{teacher_message}\n{student_answer}"
        if not _looks_like_linear_equation_lesson(text):
            return 0
        if "わかりません" in student_answer:
            return 1
        if re.search(r"答え\s*:\s*x\s*=", student_answer):
            return 3
        return 2

    def _touched_skills(self, teacher_message: str) -> set[str]:
        normalized = teacher_message.replace(" ", "").replace("　", "")
        skills = {"can_solve_ax_plus_b_equals_c"}
        if any(keyword in teacher_message for keyword in ["移項", "右辺", "左辺", "符号"]):
            skills.add("can_transpose_terms")
        if any(keyword in teacher_message for keyword in ["割", "係数", "両辺を"]):
            skills.add("can_divide_by_coefficient")
        if "-" in normalized or "マイナス" in teacher_message or "負" in teacher_message:
            skills.add("can_handle_negative_numbers")
        if "/" in normalized or "分数" in teacher_message:
            skills.add("can_handle_fractions")
        return skills


def _looks_like_linear_equation_lesson(text: str) -> bool:
    return bool(re.search(r"\d*x|x\s*[+\-=]|一次方程式|移項|係数", text))


def _coerce_score(value: Any) -> int:
    if isinstance(value, bool):
        return 80 if value else 0
    if isinstance(value, (int, float)):
        return _clamp_score(value)
    if isinstance(value, str):
        mapped = {
            "very_low": 0,
            "low": 25,
            "medium": 50,
            "high": 75,
            "very_high": 100,
            "weak": 25,
            "basic": 50,
            "sometimes": 50,
            "stable": 75,
        }
        return mapped.get(value, 0)
    return 0


def _score_to_level(score: int) -> str:
    if score < 20:
        return "very_low"
    if score < 40:
        return "low"
    if score < 60:
        return "medium"
    if score < 80:
        return "high"
    return "very_high"


def _clamp_score(value: Any) -> int:
    return max(0, min(100, int(round(value))))
