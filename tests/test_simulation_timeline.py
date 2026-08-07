from pathlib import Path

from src.experiment import export_simulation_timeline_results, run_simulation_timeline


def test_simulation_timeline_runs_mock_and_exports(tmp_path: Path):
    result = run_simulation_timeline(
        class_id="class_3_basic",
        class_size=3,
        cycles=2,
        teacher_beliefs_dir=tmp_path / "beliefs",
        logs_dir=tmp_path / "logs",
    )

    assert result["conditions"]["student_count"] == 3
    assert result["conditions"]["cycles"] == 2
    assert len(result["cycle_summary_rows"]) == 2
    assert result["research_metrics"]["phase_count"] == 10
    assert "belief_confidence_delta" in result["research_metrics"]

    outputs = export_simulation_timeline_results(result, output_dir=tmp_path)
    assert Path(outputs["json"]).exists()
    assert Path(outputs["txt"]).exists()
    assert "Simulation Timeline For Codex" in Path(outputs["txt"]).read_text(encoding="utf-8")


def test_simulation_timeline_keeps_llm_flags_off_by_default(tmp_path: Path):
    result = run_simulation_timeline(
        class_id="class_3_basic",
        class_size=3,
        cycles=1,
        teacher_beliefs_dir=tmp_path / "beliefs",
        logs_dir=tmp_path / "logs",
    )

    assert result["conditions"]["use_llm_student"] is False
    assert result["conditions"]["use_llm_communication"] is False
    assert result["conditions"]["model_id"] == "rule-based/mock"
    assert result["cycle_summary_rows"][0]["event_count"] == 15
