from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CURRICULUM_PATH = Path("data/curriculum/linear_equation.json")

DEFAULT_CONSTRAINTS = {
    "max_teacher_utterance_chars": 120,
    "next_problem_count": 1,
    "avoid_long_explanation": True,
}


class TeacherContextBuilder:
    """Builds the information a teacher AI needs before choosing a strategy."""

    def __init__(self, curriculum_path: str | Path = DEFAULT_CURRICULUM_PATH) -> None:
        self.curriculum_path = Path(curriculum_path)
        self.curriculum = self.load_curriculum(self.curriculum_path)

    @staticmethod
    def load_curriculum(path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as f:
            curriculum = json.load(f)
        if "skill_priority" not in curriculum or "lesson_goals" not in curriculum:
            raise ValueError("curriculum must include skill_priority and lesson_goals")
        return curriculum

    def build_context(
        self,
        *,
        student_state: dict[str, Any],
        recent_student_utterance: str,
        communication_observation: Any,
        classroom_observation: Any | None = None,
        target_skill: str | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        linear_state = student_state.get("knowledge_state", {}).get("linear_equation", {})
        selected_skill = target_skill or self._select_lowest_priority_skill(linear_state)
        lesson_goal = self._find_lesson_goal(selected_skill)
        observation = _observation_to_dict(communication_observation)
        merged_constraints = {**DEFAULT_CONSTRAINTS, **(constraints or {})}

        return {
            "curriculum_domain": self.curriculum.get("domain", "linear_equation"),
            "unit_title": self.curriculum.get("unit_title", "一次方程式"),
            "target_skill": selected_skill,
            "lesson_goal": lesson_goal,
            "student_state_summary": {
                "student_id": student_state.get("student_id"),
                "name": student_state.get("name"),
                "understanding": student_state.get("understanding", {}),
                "knowledge_state": linear_state,
                "error_tendency": student_state.get("error_tendency", []),
                "misconceptions": student_state.get("misconceptions", []),
                "learning_speed": student_state.get("learning_speed"),
                "personality": student_state.get("personality", {}),
                "big_five": student_state.get("big_five", {}),
                "self_efficacy": student_state.get("self_efficacy"),
                "question_tendency": student_state.get("question_tendency"),
                "motivation": student_state.get("motivation"),
                "learning_history_tail": student_state.get("learning_history", [])[-3:],
            },
            "recent_student_utterance": recent_student_utterance,
            "communication_ai_observation": observation,
            "classroom_observation": (
                _observation_to_dict(classroom_observation)
                if classroom_observation is not None
                else None
            ),
            "available_strategies": self.curriculum.get("strategy_definitions", []),
            "misconception_map": self.curriculum.get("misconception_map", {}),
            "next_problem_bank": self.curriculum.get("next_problem_bank", {}),
            "constraints": merged_constraints,
        }

    def _select_lowest_priority_skill(self, linear_state: dict[str, Any]) -> str:
        priority = self.curriculum.get("skill_priority", [])
        if not priority:
            return "can_solve_ax_plus_b_equals_c"
        return min(priority, key=lambda skill: _score(linear_state.get(skill, 0)))

    def _find_lesson_goal(self, target_skill: str) -> dict[str, Any]:
        for goal in self.curriculum.get("lesson_goals", []):
            if goal.get("target_skill") == target_skill:
                return goal
        return {
            "goal_id": target_skill,
            "target_skill": target_skill,
            "goal_text": "一次方程式の理解を深める",
            "success_criteria": [],
        }


def build_teacher_context(
    *,
    student_state: dict[str, Any],
    recent_student_utterance: str,
    communication_observation: Any,
    classroom_observation: Any | None = None,
    target_skill: str | None = None,
    constraints: dict[str, Any] | None = None,
    curriculum_path: str | Path = DEFAULT_CURRICULUM_PATH,
) -> dict[str, Any]:
    return TeacherContextBuilder(curriculum_path).build_context(
        student_state=student_state,
        recent_student_utterance=recent_student_utterance,
        communication_observation=communication_observation,
        classroom_observation=classroom_observation,
        target_skill=target_skill,
        constraints=constraints,
    )


def _score(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, min(100, value))
    return 0


def _observation_to_dict(observation: Any) -> dict[str, Any]:
    if hasattr(observation, "to_dict"):
        return observation.to_dict()
    if isinstance(observation, dict):
        return observation
    return {"raw_observation": str(observation)}
