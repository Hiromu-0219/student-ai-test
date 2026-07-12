import json

from src.assessment_logger import AssessmentLogger
from src.student_ai import StudentAISimulator
from src.test_bank import TestBank
from src.test_runner import TestRunner


def write_student(path):
    path.write_text(
        """
{
  "student_id": "S999",
  "name": "Test",
  "understanding": {"linear_equation": "basic"},
  "knowledge_state": {
    "linear_equation": {
      "level": "medium",
      "score": 50,
      "can_solve_ax_plus_b_equals_c": 70,
      "can_transpose_terms": 50,
      "can_divide_by_coefficient": 70,
      "can_handle_negative_numbers": 25,
      "can_handle_fractions": 10
    }
  },
  "error_tendency": [],
  "misconceptions": [],
  "learning_speed": "medium",
  "personality": {"confidence": "medium"},
  "big_five": {
    "openness": "medium",
    "conscientiousness": "medium",
    "extraversion": "medium",
    "agreeableness": "medium",
    "neuroticism": "medium"
  },
  "self_efficacy": "medium",
  "question_tendency": "medium",
  "motivation": "medium",
  "learning_history": []
}
""".strip(),
        encoding="utf-8",
    )


def test_test_runner_scores_and_logs_assessment(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    tests_dir = tmp_path / "tests"
    assessments_dir = tmp_path / "assessments"
    students_dir.mkdir()
    tests_dir.mkdir()
    write_student(students_dir / "S999.json")
    (tests_dir / "linear_equation_basic_001.json").write_text(
        json.dumps(
            {
                "test_id": "linear_equation_basic_001",
                "title": "Test",
                "domain": "linear_equation",
                "questions": [
                    {
                        "question_id": "Q001",
                        "problem": "2x+3=11",
                        "answer": "x = 4",
                        "skill": "can_solve_ax_plus_b_equals_c",
                        "difficulty": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    runner = TestRunner(
        simulator=sim,
        test_bank=TestBank(tests_dir),
        assessment_logger=AssessmentLogger(assessments_dir),
    )

    result = runner.run_test(student_id="S999", test_id="linear_equation_basic_001")
    updated = sim.state_manager.load_student("S999")

    assert 0 <= result["score_percentage"] <= 100
    assert result["correct_count"] in {0, 1}
    assert (assessments_dir / "machine_readable.jsonl").exists()
    assert updated["knowledge_state"]["linear_equation"]["score"] == 50
    assert updated["learning_history"] == []
    assert "assessment_directive" in result["question_results"][0]
    assert "raw_student_answer" in result["question_results"][0]


def test_test_runner_grades_controlled_answer_not_raw_llm_output(tmp_path):
    students_dir = tmp_path / "students"
    tests_dir = tmp_path / "tests"
    assessments_dir = tmp_path / "assessments"
    students_dir.mkdir()
    tests_dir.mkdir()
    write_student(students_dir / "S999.json")
    (tests_dir / "linear_equation_basic_001.json").write_text(
        json.dumps(
            {
                "test_id": "linear_equation_basic_001",
                "title": "Test",
                "domain": "linear_equation",
                "questions": [
                    {
                        "question_id": "Q001",
                        "problem": "2x+3=11",
                        "answer": "x = 4",
                        "skill": "can_solve_ax_plus_b_equals_c",
                        "difficulty": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class StubStateManager:
        def load_student(self, student_id):
            with (students_dir / f"{student_id}.json").open(encoding="utf-8") as file:
                return json.load(file)

    class StubSimulator:
        state_manager = StubStateManager()

        def respond(self, *args, **kwargs):
            return {"answer": "答え: x = 999"}

    class AlwaysCorrectCognitiveModel:
        def build_assessment_directive(self, *, student_state, question):
            return {
                "mode": "assessment",
                "target_correct": True,
                "correct_probability": 100,
                "roll": 0,
                "skill": question["skill"],
                "skill_score": 100,
                "overall_score": 100,
                "misconception_penalty": 0,
                "expected_answer": question["answer"],
                "target_answer": "x = 4",
                "rationale": "test",
            }

    runner = TestRunner(
        simulator=StubSimulator(),
        test_bank=TestBank(tests_dir),
        assessment_logger=AssessmentLogger(assessments_dir),
        cognitive_model=AlwaysCorrectCognitiveModel(),
    )

    result = runner.run_test(student_id="S999", test_id="linear_equation_basic_001")
    question_result = result["question_results"][0]

    assert result["score_percentage"] == 100.0
    assert question_result["student_answer"] == "x = 4"
    assert question_result["raw_student_answer"] == "答え: x = 999"
