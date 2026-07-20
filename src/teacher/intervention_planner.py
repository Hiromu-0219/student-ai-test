from __future__ import annotations

from typing import Any


class RuleBasedInterventionPlanner:
    """Plans whole-class and individual teacher actions without using an LLM."""

    def plan(
        self,
        *,
        classroom_observation: dict[str, Any],
        teacher_beliefs: dict[str, dict[str, Any]],
        lesson_goal: dict[str, Any],
        recent_events: list[dict[str, Any]],
        next_problem_bank: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        target_skill = lesson_goal.get("target_skill", "can_solve_ax_plus_b_equals_c")
        whole_class_plan = self._whole_class_plan(
            classroom_observation=classroom_observation,
            teacher_beliefs=teacher_beliefs,
            lesson_goal=lesson_goal,
            recent_events=recent_events,
            next_problem_bank=next_problem_bank or {},
        )
        individual_supports = [
            self._individual_support(
                student_id=student_id,
                belief=belief,
                event=_event_for_student(recent_events, student_id),
                target_skill=target_skill,
            )
            for student_id, belief in sorted(teacher_beliefs.items())
        ]
        individual_supports = [
            support for support in individual_supports if support["support_type"] != "monitor_only"
        ]
        return {
            "lesson_goal": lesson_goal,
            "whole_class_plan": whole_class_plan,
            "individual_supports": individual_supports[:5],
            "reason": self._overall_reason(classroom_observation, teacher_beliefs),
        }

    def _whole_class_plan(
        self,
        *,
        classroom_observation: dict[str, Any],
        teacher_beliefs: dict[str, dict[str, Any]],
        lesson_goal: dict[str, Any],
        recent_events: list[dict[str, Any]],
        next_problem_bank: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        target_skill = lesson_goal.get("target_skill", "can_solve_ax_plus_b_equals_c")
        low_score_count = sum(
            1
            for belief in teacher_beliefs.values()
            if _estimated_score(belief) < 45
        )
        incorrect_count = sum(1 for event in recent_events if event.get("is_correct") is False)
        low_self_count = _trait_count(teacher_beliefs, "self_efficacy", "low")
        high_anxiety_count = _trait_count(teacher_beliefs, "neuroticism", "high")
        next_problem = _select_problem(next_problem_bank, target_skill)

        if incorrect_count >= 2 or low_score_count >= 2:
            teacher_move = "全体で短い例題を1問扱い、操作を1手ずつ確認する"
            focus = lesson_goal.get("goal_text", "一次方程式の基本操作")
            pace = "slow_down"
        elif low_self_count + high_anxiety_count >= 2:
            teacher_move = "正しくできている部分を先に共有し、短い確認問題へ進む"
            focus = "不安を下げながら基本操作を確認する"
            pace = "maintain"
        else:
            teacher_move = "個人で解く時間を取り、代表者に1手順だけ説明してもらう"
            focus = lesson_goal.get("goal_text", "一次方程式の理解を深める")
            pace = "maintain_or_raise"

        return {
            "focus": focus,
            "teacher_move": teacher_move,
            "pace": pace,
            "next_problem": next_problem.get("problem"),
            "expected_answer": next_problem.get("answer"),
            "reason": (
                f"直近の誤答数={incorrect_count}、推定理解度45未満={low_score_count}、"
                f"自己効力感low={low_self_count}、不安high={high_anxiety_count}。"
            ),
        }

    def _individual_support(
        self,
        *,
        student_id: str,
        belief: dict[str, Any],
        event: dict[str, Any] | None,
        target_skill: str,
    ) -> dict[str, Any]:
        traits = belief.get("estimated_traits", {})
        score = _estimated_score(belief)
        misconceptions = belief.get("estimated_misconceptions", [])
        is_correct = event.get("is_correct") if event else None

        if _trait_level(traits, "self_efficacy") == "low" or _trait_level(traits, "neuroticism") == "high":
            return {
                "student_id": student_id,
                "support_type": "confidence_support",
                "teacher_move": "最初にできている部分を短く返し、その後に1点だけ確認する",
                "target_skill": target_skill,
                "reason": "自己効力感の低さ、または不安傾向が推定されているため",
            }
        if is_correct is False or score < 45:
            return {
                "student_id": student_id,
                "support_type": "micro_practice",
                "teacher_move": "同じ型の小問題を1問出し、途中式を1行書かせる",
                "target_skill": target_skill,
                "reason": f"推定理解度={score}、直近正誤={is_correct} のため",
            }
        if misconceptions:
            return {
                "student_id": student_id,
                "support_type": "misconception_check",
                "teacher_move": "誤りやすい操作について、正しい操作との違いを確認する",
                "target_skill": target_skill,
                "reason": misconceptions[0].get("name", "誤概念の可能性があるため"),
            }
        if is_correct is True and score >= 60:
            return {
                "student_id": student_id,
                "support_type": "extension",
                "teacher_move": "少し数値を変えた発展問題を出し、解法を短く説明させる",
                "target_skill": target_skill,
                "reason": f"直近正答かつ推定理解度={score} のため",
            }
        return {
            "student_id": student_id,
            "support_type": "monitor_only",
            "teacher_move": "全体指導の中で反応を観察する",
            "target_skill": target_skill,
            "reason": "個別介入の優先度が高くないため",
        }

    def _overall_reason(
        self,
        classroom_observation: dict[str, Any],
        teacher_beliefs: dict[str, dict[str, Any]],
    ) -> str:
        summary = classroom_observation.get("classroom_summary", "")
        observed_count = classroom_observation.get("student_count", len(teacher_beliefs))
        return f"{observed_count}人分の観察とteacher_beliefに基づいて計画。{summary}"


def _estimated_score(belief: dict[str, Any]) -> int:
    return int(
        belief.get("estimated_knowledge", {})
        .get("linear_equation", {})
        .get("score", 50)
    )


def _trait_level(traits: dict[str, Any], key: str) -> str:
    value = traits.get(key, {})
    if isinstance(value, dict):
        return str(value.get("level", "medium"))
    return str(value or "medium")


def _trait_count(
    teacher_beliefs: dict[str, dict[str, Any]],
    trait_key: str,
    level: str,
) -> int:
    return sum(
        1
        for belief in teacher_beliefs.values()
        if _trait_level(belief.get("estimated_traits", {}), trait_key) == level
    )


def _event_for_student(
    recent_events: list[dict[str, Any]],
    student_id: str,
) -> dict[str, Any] | None:
    for event in reversed(recent_events):
        if event.get("student_id") == student_id:
            return event
    return None


def _select_problem(
    next_problem_bank: dict[str, list[dict[str, Any]]],
    target_skill: str,
) -> dict[str, Any]:
    problems = next_problem_bank.get(target_skill) or next_problem_bank.get(
        "can_solve_ax_plus_b_equals_c",
        [],
    )
    return problems[0] if problems else {"problem": None, "answer": None}
