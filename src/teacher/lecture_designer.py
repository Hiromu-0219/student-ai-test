from __future__ import annotations

from typing import Any

from src.teacher.lesson_planner import RuleBasedLessonPlanner


class RuleBasedLectureDesignAI:
    """Design a whole-class lecture from observable classroom estimates.

    The design AI must not read true student states. Its input is teacher belief:
    an estimated view built from classroom observations and CommunicationAI
    summaries.
    """

    def __init__(self, lesson_planner: RuleBasedLessonPlanner | None = None) -> None:
        self.lesson_planner = lesson_planner or RuleBasedLessonPlanner()

    def design_lecture(
        self,
        *,
        teacher_beliefs: dict[str, dict[str, Any]],
        curriculum: dict[str, Any],
        total_minutes: int = 30,
        lecture_id: str | None = None,
    ) -> dict[str, Any]:
        lesson_plan = self.lesson_planner.plan_lesson(
            teacher_beliefs=teacher_beliefs,
            curriculum=curriculum,
            total_minutes=total_minutes,
        )
        class_profile = lesson_plan["class_profile"]
        return {
            "lecture_id": lecture_id,
            "role": "lecture_design_ai",
            "objective": "optimize_whole_class_lecture_from_observable_estimates",
            "observable_input_policy": {
                "uses": [
                    "teacher_beliefs.estimated_knowledge",
                    "teacher_beliefs.estimated_traits",
                    "teacher_beliefs.estimated_misconceptions",
                    "teacher_beliefs.evidence_history",
                    "curriculum",
                    "total_minutes",
                ],
                "does_not_use": [
                    "true_student_knowledge_state",
                    "true_student_misconceptions",
                    "true_student_personality",
                    "true_student_motivation",
                    "raw_hidden_student_parameters",
                ],
            },
            "class_diagnosis": _class_diagnosis(class_profile),
            "optimization_targets": _optimization_targets(class_profile),
            "recommended_lecture": {
                "lesson_goal": lesson_plan["lesson_goal"],
                "lesson_structure": lesson_plan["lesson_structure"],
                "whole_class_policy": _whole_class_policy(class_profile, lesson_plan),
                "individual_support_policy": lesson_plan["individual_support_policy"],
            },
            "lesson_plan": lesson_plan,
            "reason": lesson_plan.get("reason"),
        }


def _class_diagnosis(class_profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "student_count": class_profile.get("student_count", 0),
        "average_estimated_score": class_profile.get("average_estimated_score"),
        "score_std": class_profile.get("score_std"),
        "low_score_count": len(class_profile.get("low_score_students", [])),
        "high_score_count": len(class_profile.get("high_score_students", [])),
        "common_misconceptions": class_profile.get("common_misconceptions", []),
        "common_risks": class_profile.get("common_risks", []),
        "trait_counts": class_profile.get("trait_counts", {}),
    }


def _optimization_targets(class_profile: dict[str, Any]) -> list[str]:
    targets = ["raise_class_level_understanding"]
    if class_profile.get("score_std", 0) >= 12:
        targets.append("reduce_between_student_gap")
    if class_profile.get("low_score_students"):
        targets.append("support_low_estimated_understanding_students")
    if class_profile.get("common_misconceptions"):
        targets.append("address_common_misconceptions")
    trait_counts = class_profile.get("trait_counts", {})
    if trait_counts.get("question_tendency", {}).get("low", 0) >= 2:
        targets.append("increase_teacher_initiated_check_questions")
    if trait_counts.get("self_efficacy", {}).get("low", 0) >= 2:
        targets.append("protect_self_efficacy")
    return targets


def _whole_class_policy(
    class_profile: dict[str, Any],
    lesson_plan: dict[str, Any],
) -> dict[str, Any]:
    target_skill = lesson_plan.get("lesson_goal", {}).get("target_skill")
    low_ratio = 0.0
    student_count = int(class_profile.get("student_count", 0) or 0)
    if student_count:
        low_ratio = len(class_profile.get("low_score_students", [])) / student_count

    if low_ratio >= 0.5:
        pace = "slow"
        strategy = ["short_review", "worked_example", "guided_practice"]
    elif class_profile.get("score_std", 0) >= 12:
        pace = "adaptive"
        strategy = ["brief_explanation", "individual_practice", "targeted_support"]
    else:
        pace = "standard"
        strategy = ["brief_explanation", "worked_example", "practice"]

    if class_profile.get("common_misconceptions"):
        strategy.append("misconception_confrontation")

    return {
        "target_skill": target_skill,
        "pace": pace,
        "strategy": strategy,
        "reason": "selected from class-level observable estimates",
    }
