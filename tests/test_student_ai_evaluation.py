import shutil
from pathlib import Path

from src.experiment import (
    compare_cognitive_models,
    export_cognitive_model_comparison_for_codex,
    export_student_ai_evaluation,
    export_student_ai_evaluation_for_codex,
    run_student_ai_evaluation,
)


def test_student_ai_evaluation_runs_core_student_experiments(tmp_path):
    students_dir = tmp_path / "students"
    tests_dir = tmp_path / "tests"
    shutil.copytree(Path("data/students"), students_dir)
    shutil.copytree(Path("data/tests"), tests_dir)

    result = run_student_ai_evaluation(
        student_id="S001",
        test_id="linear_equation_20q_001",
        understanding_levels=[0, 50, 100],
        students_dir=students_dir,
        tests_dir=tests_dir,
        logs_dir=tmp_path / "logs",
        use_mock_model=True,
    )

    assert result["question_count"] == 20
    assert [row["understanding"] for row in result["learning_curve"]] == [0, 50, 100]
    assert result["learning_curve"][0]["average_correct_probability"] < result["learning_curve"][-1]["average_correct_probability"]
    assert result["misconception_comparison"]["rows"]
    assert "related_probability_gap" in result["misconception_comparison"]["rows"][0]
    assert result["skill_breakdown"]
    assert "target_probability_drop" in result["skill_breakdown"][0]
    assert result["difficulty_breakdown"]
    assert "average_correct_probability" in result["difficulty_breakdown"][0]
    assert result["parameter_guide"]
    assert result["summary"]["difficulty_rows"] == len(result["difficulty_breakdown"])
    assert len(result["utterance_samples"]) == 3
    assert result["human_replacement_validity"]["overall_score"] >= 0
    assert result["human_replacement_validity"]["overall_score"] <= 0.95
    assert result["human_replacement_validity"]["evidence_level"] == "internal_validity_only"
    assert result["summary"]["internal_validity_score"] == result["human_replacement_validity"]["overall_score"]
    assert result["summary"]["evidence_level"] == "internal_validity_only"
    assert result["summary"]["human_replacement_verdict"]
    assert all("答え: x = 4" in sample["utterance"] for sample in result["utterance_samples"])

    output_path = export_student_ai_evaluation(
        result,
        output_path=tmp_path / "student_ai_eval.txt",
    )
    assert output_path.exists()
    assert "Student AI Evaluation Summary" in output_path.read_text(encoding="utf-8")

    codex_path = export_student_ai_evaluation_for_codex(
        result,
        output_path=tmp_path / "student_ai_eval_for_codex.txt",
    )
    codex_text = codex_path.read_text(encoding="utf-8")
    assert "Student AI Evaluation For Codex" in codex_text
    assert "Internal Validity Evaluation" in codex_text
    assert "internal_validity_score" in codex_text
    assert "evidence_level" in codex_text
    assert "Auto Interpretation" in codex_text
    assert "Learning Curve" in codex_text
    assert "related_probability_gap" in codex_text
    assert "target_probability_drop" in codex_text
    assert "Parameter Guide" in codex_text
    assert "Difficulty Breakdown" in codex_text
    assert "Utterance Samples" in codex_text


def test_cognitive_model_comparison_runs(tmp_path):
    students_dir = tmp_path / "students"
    tests_dir = tmp_path / "tests"
    shutil.copytree(Path("data/students"), students_dir)
    shutil.copytree(Path("data/tests"), tests_dir)

    result = compare_cognitive_models(
        student_id="S001",
        test_id="linear_equation_20q_001",
        understanding_levels=[0, 50, 100],
        students_dir=students_dir,
        tests_dir=tests_dir,
        logs_dir=tmp_path / "logs",
        use_mock_model=True,
    )

    assert set(result["models"]) == {"legacy", "bkt_irt"}
    assert len(result["learning_curve_comparison"]) == 3
    assert result["summary"]["model_pair"] == "legacy_vs_bkt_irt"
    assert "probability_delta" in result["learning_curve_comparison"][0]
    assert result["models"]["bkt_irt"]["difficulty_breakdown"]

    output_path = export_cognitive_model_comparison_for_codex(
        result,
        output_path=tmp_path / "cognitive_model_comparison.txt",
    )
    text = output_path.read_text(encoding="utf-8")
    assert "Cognitive Model Comparison For Codex" in text
    assert "legacy_accuracy" in text
    assert "bkt_irt_accuracy" in text
    assert "Difficulty Breakdown By Model" in text
