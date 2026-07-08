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
  "error_tendency": [],
  "personality": {"confidence": "medium"},
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
