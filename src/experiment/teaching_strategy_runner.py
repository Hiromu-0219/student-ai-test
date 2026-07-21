from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.class_manager import ClassManager
from src.experiment.experiment_config import TeachingStrategyExperimentConfig
from src.student_ai import StudentAISimulator
from src.teacher import LessonSessionRunner, RuleBasedLessonPlanner
from src.teacher.belief_manager import TeacherBeliefManager


def run_teaching_strategy_experiment(
    config: TeachingStrategyExperimentConfig | None = None,
) -> dict[str, Any]:
    """Run the core multi-student teaching strategy experiment.

    The experiment flow is:
    1. Load a class and curriculum.
    2. Build initial teacher beliefs for visible classroom use.
    3. Plan a lesson from the class-level belief profile.
    4. Run the lesson session.
    5. Return compact summaries for notebook display or export.
    """

    config = config or TeachingStrategyExperimentConfig()
    curriculum = _load_json(config.curriculum_path)
    class_manager = ClassManager(
        classes_dir=config.classes_dir,
        students_dir=config.students_dir,
    )
    class_state = class_manager.load_class(config.class_id)
    student_ids = class_state["student_ids"]

    belief_manager = TeacherBeliefManager(config.teacher_beliefs_dir)
    initial_teacher_beliefs = {
        student_id: belief_manager.load_or_create(config.teacher_id, student_id)
        for student_id in student_ids
    }
    lesson_plan = RuleBasedLessonPlanner().plan_lesson(
        teacher_beliefs=initial_teacher_beliefs,
        curriculum=curriculum,
        total_minutes=config.total_minutes,
    )
    student_simulator = StudentAISimulator(
        use_mock_model=config.use_mock_student,
        model_id=config.model_id,
        students_dir=config.students_dir,
        logs_dir=config.logs_dir,
        generation_config=config.generation_config,
        model_load_config=config.model_load_config,
    )
    session_result = LessonSessionRunner(
        student_simulator=student_simulator,
        belief_manager=belief_manager,
        teacher_id=config.teacher_id,
        update_student_knowledge=config.update_student_knowledge,
    ).run_lesson(
        lesson_id=f"{config.class_id}_core_lesson",
        student_ids=student_ids,
        lesson_plan=lesson_plan,
        curriculum=curriculum,
        initial_teacher_beliefs=initial_teacher_beliefs,
    )

    return {
        "config": config,
        "class_state": class_state,
        "student_ids": student_ids,
        "lesson_plan": lesson_plan,
        "session_result": session_result,
        "phase_summary": summarize_phases(session_result),
        "summary": session_result["summary"],
    }


def summarize_phases(session_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for turn in session_result.get("turns", []):
        events = turn.get("events", [])
        graded_events = [event for event in events if event.get("is_correct") is not None]
        correct_count = sum(1 for event in graded_events if event.get("is_correct") is True)
        individual_message_count = sum(
            1
            for event in events
            if event.get("teacher_prompt") != turn.get("teacher_message")
        )
        rows.append(
            {
                "phase_index": turn.get("phase_index"),
                "phase": turn.get("phase", {}).get("phase"),
                "minutes": turn.get("phase", {}).get("minutes"),
                "student_events": len(events),
                "expected_answer": turn.get("expected_answer"),
                "correct_count": correct_count,
                "accuracy": round(correct_count / len(graded_events), 3)
                if graded_events
                else None,
                "individual_message_count": individual_message_count,
            }
        )
    return rows


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
