import shutil
from pathlib import Path

from src.student_ai import StudentAISimulator
from src.teacher import LessonSessionRunner
from src.teacher.belief_manager import TeacherBeliefManager


def _curriculum():
    return {
        "lesson_goals": [
            {
                "target_skill": "can_divide_by_coefficient",
                "goal_text": "係数で両辺を割って x を求める",
                "success_criteria": [],
            }
        ],
        "next_problem_bank": {
            "can_divide_by_coefficient": [
                {"problem": "3x = 15", "answer": "x = 5"},
                {"problem": "5x = 20", "answer": "x = 4"},
            ]
        },
    }


def _lesson_plan():
    return {
        "lesson_goal": {
            "target_skill": "can_divide_by_coefficient",
            "goal_text": "係数で両辺を割って x を求める",
        },
        "lesson_structure": [
            {"phase": "導入", "minutes": 3, "purpose": "目標共有"},
            {"phase": "全体説明", "minutes": 5, "purpose": "説明"},
            {
                "phase": "例題",
                "minutes": 5,
                "problem": "3x = 15",
                "expected_answer": "x = 5",
            },
            {"phase": "個別演習", "minutes": 11, "purpose": "演習"},
            {
                "phase": "確認",
                "minutes": 6,
                "problem": "5x = 20",
                "expected_answer": "x = 4",
            },
        ],
    }


def test_lesson_session_runner_executes_all_phases(tmp_path):
    students_dir = tmp_path / "students"
    shutil.copytree(Path("data/students"), students_dir)
    simulator = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(tmp_path / "logs"),
        use_mock_model=True,
    )
    belief_manager = TeacherBeliefManager(tmp_path / "teacher_beliefs")
    runner = LessonSessionRunner(
        student_simulator=simulator,
        belief_manager=belief_manager,
        teacher_id="T_TEST",
    )

    result = runner.run_lesson(
        lesson_id="LESSON_TEST",
        student_ids=["S001", "S002", "S003"],
        lesson_plan=_lesson_plan(),
        curriculum=_curriculum(),
    )

    assert result["lesson_id"] == "LESSON_TEST"
    assert len(result["turns"]) == 5
    assert result["summary"]["turn_count"] == 5
    assert result["summary"]["graded_event_count"] == 6
    assert set(result["final_teacher_beliefs"]) == {"S001", "S002", "S003"}
    assert result["final_class_profile"]["student_count"] == 3
    for turn in result["turns"]:
        assert len(turn["events"]) == 3
        assert turn["classroom_observation"]["student_count"] == 3
