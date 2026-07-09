from src.student_ai import StudentAISimulator


def test_simulator_mock_answer_logs_and_updates_history(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    (students_dir / "S999.json").write_text(
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

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    result = sim.answer("S999", "2x+3=11")

    assert "答え: x = 4" in result["answer"]
    assert (logs_dir / "machine_readable.jsonl").exists()
    assert "2x+3=11" in (logs_dir / "human_readable.md").read_text(encoding="utf-8")
    assert "learning_history" in (students_dir / "S999.json").read_text(encoding="utf-8")


def test_simulator_mock_respond_accepts_teacher_message(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    (students_dir / "S999.json").write_text(
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

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    result = sim.respond("S999", "今日は 2x+3=11 を一緒に解こう")

    assert result["metadata"]["interaction_type"] == "lesson_dialogue"
    assert "答え: x = 4" in result["answer"]


def test_simulator_updates_knowledge_state_after_interaction(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    (students_dir / "S999.json").write_text(
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

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    sim.respond("S999", "2x+3=11 を解いてください")
    updated = sim.state_manager.load_student("S999")

    assert updated["knowledge_state"]["linear_equation"]["score"] > 50
    assert updated["learning_history"][-1]["learning_event"]["knowledge_delta"] > 0
