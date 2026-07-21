from src.student_ai import StudentAISimulator


def _write_student(path, *, score=50, misconceptions=None):
    misconceptions = misconceptions or []
    path.write_text(
        f"""
{{
  "student_id": "S999",
  "name": "Test",
  "understanding": {{"linear_equation": "basic"}},
  "knowledge_state": {{
    "linear_equation": {{
      "level": "medium",
      "score": {score},
      "can_solve_ax_plus_b_equals_c": {score},
      "can_transpose_terms": {score},
      "can_divide_by_coefficient": {score},
      "can_handle_negative_numbers": 25,
      "can_handle_fractions": 10
    }}
  }},
  "error_tendency": [],
  "misconceptions": {misconceptions!r},
  "learning_speed": "medium",
  "personality": {{"confidence": "medium"}},
  "big_five": {{
    "openness": "medium",
    "conscientiousness": "medium",
    "extraversion": "medium",
    "agreeableness": "medium",
    "neuroticism": "medium"
  }},
  "self_efficacy": "medium",
  "question_tendency": "medium",
  "motivation": "medium",
  "learning_history": []
}}
""".strip().replace("'", '"'),
        encoding="utf-8",
    )


def test_simulator_mock_answer_logs_and_updates_history(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    _write_student(students_dir / "S999.json", score=70)

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
    _write_student(students_dir / "S999.json", score=70)

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
    _write_student(students_dir / "S999.json", score=50)

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    sim.respond("S999", "2x+3=11 を解いてください")
    updated = sim.state_manager.load_student("S999")

    assert updated["knowledge_state"]["linear_equation"]["score"] > 50
    assert updated["learning_history"][-1]["learning_event"]["knowledge_delta"] > 0


def test_simulator_apply_learning_intervention_resolves_misconceptions(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    _write_student(
        students_dir / "S999.json",
        score=30,
        misconceptions=[
            "移項しても符号は変えなくてよいと思っている",
            "係数で割る代わりに係数を引くことがある",
        ],
    )

    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    event = sim.apply_learning_intervention(
        "S999",
        skill_deltas={
            "score": 20,
            "can_transpose_terms": 30,
            "can_divide_by_coefficient": 30,
        },
    )
    updated = sim.state_manager.load_student("S999")

    assert updated["knowledge_state"]["linear_equation"]["score"] == 50
    assert updated["knowledge_state"]["linear_equation"]["can_transpose_terms"] == 60
    assert updated["misconceptions"] == []
    assert len(event["resolved_misconceptions"]) == 2


def test_assessment_response_uses_answer_only_format(tmp_path):
    students_dir = tmp_path / "students"
    logs_dir = tmp_path / "logs"
    students_dir.mkdir()
    _write_student(students_dir / "S999.json", score=50)
    sim = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=True,
    )
    result = sim.respond(
        "S999",
        "2x+3=11",
        update_knowledge=False,
        assessment_directive={
            "mode": "assessment",
            "target_correct": True,
            "target_answer": "x = 4",
            "correct_probability": 100,
            "rationale": "test",
        },
    )

    assert result["answer"] == "答え: x = 4"
