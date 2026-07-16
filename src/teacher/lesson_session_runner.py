from __future__ import annotations

import time
from typing import Any

from src.grader import LinearEquationGrader
from src.observer.observation_filter import (
    build_observable_event,
    events_to_communication_rows,
)
from src.observer.trait_classifier import CommunicationAI
from src.student_ai import StudentAISimulator
from src.teacher.belief_manager import TeacherBeliefManager
from src.teacher.lesson_planner import RuleBasedLessonPlanner


class LessonSessionRunner:
    """Runs a planned lesson structure across multiple students.

    The runner is intentionally thin: it does not decide the lesson plan. It
    executes each phase, records observable events, asks CommunicationAI to
    summarize the class, and updates teacher_belief from observable evidence.
    """

    def __init__(
        self,
        *,
        student_simulator: StudentAISimulator | None = None,
        communication_ai: CommunicationAI | None = None,
        belief_manager: TeacherBeliefManager | None = None,
        grader: LinearEquationGrader | None = None,
        teacher_id: str = "T001",
        update_student_knowledge: bool = False,
    ) -> None:
        self.student_simulator = student_simulator or StudentAISimulator(use_mock_model=True)
        self.communication_ai = communication_ai or CommunicationAI()
        self.belief_manager = belief_manager or TeacherBeliefManager()
        self.grader = grader or LinearEquationGrader()
        self.teacher_id = teacher_id
        self.update_student_knowledge = update_student_knowledge

    def run_lesson(
        self,
        *,
        lesson_id: str,
        student_ids: list[str],
        lesson_plan: dict[str, Any],
        curriculum: dict[str, Any],
    ) -> dict[str, Any]:
        if not student_ids:
            raise ValueError("student_ids must not be empty")

        lesson_goal = lesson_plan.get("lesson_goal", {})
        support_policy_by_student = _support_policy_by_student(
            lesson_plan.get("individual_support_policy", [])
        )
        turns = []
        latest_beliefs: dict[str, dict[str, Any]] = {
            student_id: self.belief_manager.load_or_create(self.teacher_id, student_id)
            for student_id in student_ids
        }

        for phase_index, phase in enumerate(lesson_plan.get("lesson_structure", []), start=1):
            teacher_message = self._teacher_message_for_phase(
                phase=phase,
                lesson_goal=lesson_goal,
                curriculum=curriculum,
            )
            student_teacher_messages = self._student_teacher_messages(
                student_ids=student_ids,
                phase=phase,
                teacher_message=teacher_message,
                support_policy_by_student=support_policy_by_student,
            )
            expected_answer = phase.get("expected_answer")
            events = self._run_phase_for_students(
                lesson_id=f"{lesson_id}_P{phase_index:02d}",
                student_ids=student_ids,
                student_teacher_messages=student_teacher_messages,
                expected_answer=expected_answer,
            )
            classroom_observation = self.communication_ai.summarize_classroom(
                events_to_communication_rows(events),
                min_students=min(3, len(student_ids)),
                max_students=20,
            ).to_dict()
            latest_beliefs = self.belief_manager.update_many(
                teacher_id=self.teacher_id,
                observations=events,
                communication_results=classroom_observation["individual_results"],
            )
            turns.append(
                {
                    "phase_index": phase_index,
                    "phase": phase,
                    "teacher_message": teacher_message,
                    "student_teacher_messages": student_teacher_messages,
                    "expected_answer": expected_answer,
                    "events": events,
                    "classroom_observation": classroom_observation,
                    "teacher_beliefs": latest_beliefs,
                }
            )

        final_class_profile = RuleBasedLessonPlanner().build_class_profile(latest_beliefs)
        return {
            "lesson_id": lesson_id,
            "teacher_id": self.teacher_id,
            "student_ids": student_ids,
            "lesson_goal": lesson_goal,
            "turns": turns,
            "final_teacher_beliefs": latest_beliefs,
            "final_class_profile": final_class_profile,
            "summary": self._session_summary(turns, final_class_profile),
        }

    def _run_phase_for_students(
        self,
        *,
        lesson_id: str,
        student_ids: list[str],
        student_teacher_messages: dict[str, str],
        expected_answer: str | None,
    ) -> list[dict[str, Any]]:
        events = []
        for student_id in student_ids:
            teacher_message = student_teacher_messages[student_id]
            started = time.perf_counter()
            record = self.student_simulator.respond(
                student_id,
                teacher_message,
                update_knowledge=self.update_student_knowledge,
            )
            response_time_sec = round(time.perf_counter() - started, 2)
            answer = record["answer"]
            grade = (
                self.grader.grade(expected_answer, answer)
                if expected_answer
                else {
                    "is_correct": None,
                    "score": None,
                    "expected_value": None,
                    "student_value": None,
                }
            )
            event = build_observable_event(
                lesson_id=lesson_id,
                teacher_id=self.teacher_id,
                student_id=student_id,
                teacher_prompt=teacher_message,
                utterance=answer,
                answer=answer,
                is_correct=grade["is_correct"],
                response_time_sec=response_time_sec,
            ).to_dict()
            event["grade"] = grade
            events.append(event)
        return events

    def _student_teacher_messages(
        self,
        *,
        student_ids: list[str],
        phase: dict[str, Any],
        teacher_message: str,
        support_policy_by_student: dict[str, str],
    ) -> dict[str, str]:
        messages = {student_id: teacher_message for student_id in student_ids}
        if not _is_individual_practice_phase(phase):
            return messages

        for student_id in student_ids:
            policy = support_policy_by_student.get(student_id)
            if policy:
                messages[student_id] = f"{teacher_message}\n個別支援: {policy}"
        return messages

    def _teacher_message_for_phase(
        self,
        *,
        phase: dict[str, Any],
        lesson_goal: dict[str, Any],
        curriculum: dict[str, Any],
    ) -> str:
        phase_name = str(phase.get("phase", "lesson"))
        goal_text = str(lesson_goal.get("goal_text", "一次方程式を解く"))
        problem = phase.get("problem")
        if not problem and phase_name in {"個別演習", "確認"}:
            problem = _first_problem_for_goal(lesson_goal, curriculum)

        if phase_name == "導入":
            return f"今日の目標は「{goal_text}」です。まず前回の考え方を短く確認しましょう。"
        if phase_name == "全体説明":
            return f"全体説明です。{goal_text} ために、式の左右で同じ操作をすることを確認します。"
        if phase_name == "例題":
            return f"例題です。{problem} を1手ずつ考えて、答えを書いてください。"
        if phase_name == "個別演習":
            return f"個別演習です。{problem} を自分で解いて、途中で迷ったらその点も書いてください。"
        if phase_name == "確認":
            return f"確認問題です。{problem} を解いて、答えだけでなく確認した点も短く書いてください。"
        return f"{phase_name}です。{goal_text} について考えてください。"

    def _session_summary(
        self,
        turns: list[dict[str, Any]],
        final_class_profile: dict[str, Any],
    ) -> dict[str, Any]:
        graded_events = [
            event
            for turn in turns
            for event in turn["events"]
            if event.get("is_correct") is not None
        ]
        correct_count = sum(1 for event in graded_events if event.get("is_correct") is True)
        total_count = len(graded_events)
        return {
            "turn_count": len(turns),
            "graded_event_count": total_count,
            "correct_count": correct_count,
            "accuracy": round(correct_count / total_count, 3) if total_count else None,
            "final_average_estimated_score": final_class_profile.get(
                "average_estimated_score"
            ),
            "final_common_risks": final_class_profile.get("common_risks", []),
        }


def _first_problem_for_goal(
    lesson_goal: dict[str, Any],
    curriculum: dict[str, Any],
) -> str | None:
    target_skill = lesson_goal.get("target_skill", "can_solve_ax_plus_b_equals_c")
    problems = curriculum.get("next_problem_bank", {}).get(target_skill, [])
    if not problems:
        return None
    return problems[0].get("problem")


def _support_policy_by_student(
    individual_support_policy: list[dict[str, Any]],
) -> dict[str, str]:
    policies = {}
    for item in individual_support_policy:
        student_id = str(item.get("student_id", ""))
        policy = str(item.get("policy", ""))
        if student_id and policy:
            policies[student_id] = policy
    return policies


def _is_individual_practice_phase(phase: dict[str, Any]) -> bool:
    phase_name = str(phase.get("phase", ""))
    return (
        phase_name == "個別演習"
        or "個別演習" in phase_name
        or "individual" in phase_name.lower()
        or "practice" in phase_name.lower()
    )
