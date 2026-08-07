from pathlib import Path

from src.experiment import (
    export_lesson_design_validity_for_codex,
    run_lesson_design_validity_evaluation,
)


def test_lesson_design_validity_changes_design_by_scenario():
    result = run_lesson_design_validity_evaluation()

    assert result["summary"]["scenario_count"] == 4
    assert result["summary"]["passed_checks"] == result["summary"]["total_checks"]

    rows = {row["scenario"]: row for row in result["comparison_rows"]}
    assert rows["low_understanding_class"]["goal"] == "can_transpose_terms"
    assert rows["high_understanding_class"]["goal"] == "can_divide_by_coefficient"
    assert rows["common_misconception_class"]["goal"] == "can_divide_by_coefficient"
    assert rows["low_understanding_class"]["whole_explanation_min"] > rows["high_understanding_class"]["whole_explanation_min"]
    assert rows["wide_gap_class"]["pace"] == "adaptive"


def test_lesson_design_validity_exports_codex_txt(tmp_path: Path):
    result = run_lesson_design_validity_evaluation()
    output = export_lesson_design_validity_for_codex(
        result,
        output_path=tmp_path / "lesson_design_validity_for_codex.txt",
    )

    text = output.read_text(encoding="utf-8")
    assert "# Lesson Design Validity Evaluation For Codex" in text
    assert "## Scenario Comparison" in text
    assert "low_understanding_class" in text
    assert "whole_class_optimization_targets" in text
