from pathlib import Path

from src.experiment import (
    export_communication_validity_for_codex,
    run_communication_validity_evaluation,
)


def test_communication_validity_uses_observable_rows_only():
    result = run_communication_validity_evaluation(class_id="class_10_mixed")

    assert result["student_count"] == 10
    assert result["summary"]["total_checks"] == 5
    assert result["summary"]["passed_checks"] >= 3

    hidden_keys = {
        "knowledge_state",
        "self_efficacy",
        "question_tendency",
        "motivation",
        "big_five",
        "misconceptions",
        "correct_probability",
    }
    for row in result["observable_rows"]:
        assert set(row) == {"student_id", "answer", "observable_event"}
        assert not hidden_keys & set(row["observable_event"])


def test_communication_validity_exports_codex_txt(tmp_path: Path):
    result = run_communication_validity_evaluation(class_id="class_3_basic")
    output = export_communication_validity_for_codex(
        result,
        output_path=tmp_path / "communication_validity_for_codex.txt",
    )

    text = output.read_text(encoding="utf-8")
    assert "# Communication AI Validity Evaluation For Codex" in text
    assert "## Trait Accuracy" in text
    assert "## Per-student Comparison" in text
    assert "observable_input_only" in text
