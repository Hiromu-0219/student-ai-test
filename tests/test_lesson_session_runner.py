import shutil
from pathlib import Path

from src.student_ai import StudentAISimulator
from src.teacher import LessonSessionRunner, RuleBasedLessonPlanner
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


def test_lesson_session_runner_delivers_individual_support_only_in_practice(tmp_path):
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
    lesson_plan = _lesson_plan()
    lesson_plan["lesson_structure"][3]["phase"] = "individual_practice"
    lesson_plan["individual_support_policy"] = [
        {
            "student_id": "S001",
            "target_skill": "can_divide_by_coefficient",
            "policy": "check the first step before continuing",
        }
    ]

    result = runner.run_lesson(
        lesson_id="LESSON_TEST",
        student_ids=["S001", "S002", "S003"],
        lesson_plan=lesson_plan,
        curriculum=_curriculum(),
    )

    introduction_turn = result["turns"][0]
    practice_turn = result["turns"][3]

    assert introduction_turn["student_teacher_messages"]["S001"] == introduction_turn["teacher_message"]
    assert "個別支援" in practice_turn["student_teacher_messages"]["S001"]
    assert "check the first step" in practice_turn["student_teacher_messages"]["S001"]
    assert practice_turn["student_teacher_messages"]["S002"] == practice_turn["teacher_message"]
    s001_event = next(
        event for event in practice_turn["events"] if event["student_id"] == "S001"
    )
    assert "check the first step" in s001_event["teacher_prompt"]


def test_lesson_session_runner_uses_lesson_planner_individual_practice_phase(tmp_path):
    students_dir = tmp_path / "students"
    shutil.copytree(Path("data/students"), students_dir)
    simulator = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(tmp_path / "logs"),
        use_mock_model=True,
    )
    belief_manager = TeacherBeliefManager(tmp_path / "teacher_beliefs")
    teacher_beliefs = {
        "S001": belief_manager.load_or_create("T_TEST", "S001"),
        "S002": belief_manager.load_or_create("T_TEST", "S002"),
        "S003": belief_manager.load_or_create("T_TEST", "S003"),
    }
    teacher_beliefs["S001"]["estimated_traits"]["question_tendency"]["level"] = "low"
    lesson_plan = RuleBasedLessonPlanner().plan_lesson(
        teacher_beliefs=teacher_beliefs,
        curriculum=_curriculum(),
        total_minutes=30,
    )
    runner = LessonSessionRunner(
        student_simulator=simulator,
        belief_manager=belief_manager,
        teacher_id="T_TEST",
    )

    result = runner.run_lesson(
        lesson_id="LESSON_TEST",
        student_ids=["S001", "S002", "S003"],
        lesson_plan=lesson_plan,
        curriculum=_curriculum(),
    )

    individual_message_counts = [
        sum(
            1
            for event in turn["events"]
            if event["teacher_prompt"] != turn["teacher_message"]
        )
        for turn in result["turns"]
    ]
    assert max(individual_message_counts) >= 1


def test_lesson_session_runner_can_start_from_existing_teacher_beliefs(tmp_path):
    students_dir = tmp_path / "students"
    shutil.copytree(Path("data/students"), students_dir)
    simulator = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(tmp_path / "logs"),
        use_mock_model=True,
    )
    belief_manager = TeacherBeliefManager(tmp_path / "teacher_beliefs")
    initial_beliefs = {
        student_id: belief_manager.load_or_create("T_TEST", student_id)
        for student_id in ["S001", "S002", "S003"]
    }
    for belief in initial_beliefs.values():
        belief["estimated_knowledge"]["linear_equation"]["score"] = 68
        belief["estimated_knowledge"]["linear_equation"]["confidence"] = 0.4
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
        initial_teacher_beliefs=initial_beliefs,
    )

    assert result["final_class_profile"]["average_estimated_score"] > 68
    assert len(result["final_class_profile"]["high_score_students"]) >= 2
    assert set(result["final_class_profile"]["high_score_students"]).issubset(
        {"S001", "S002", "S003"}
    )
