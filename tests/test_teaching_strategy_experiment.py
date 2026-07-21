import shutil
from pathlib import Path

from src.experiment import (
    TeachingStrategyExperimentConfig,
    export_teaching_strategy_summary,
    run_teaching_strategy_experiment,
)


def test_teaching_strategy_experiment_runs_with_mock_model(tmp_path):
    students_dir = tmp_path / "students"
    classes_dir = tmp_path / "classes"
    shutil.copytree(Path("data/students"), students_dir)
    shutil.copytree(Path("data/classes"), classes_dir)

    result = run_teaching_strategy_experiment(
        TeachingStrategyExperimentConfig(
            class_id="class_3_basic",
            teacher_id="T_TEST_EXPERIMENT",
            classes_dir=str(classes_dir),
            students_dir=str(students_dir),
            logs_dir=str(tmp_path / "logs"),
            teacher_beliefs_dir=str(tmp_path / "teacher_beliefs"),
            use_mock_student=True,
        )
    )

    assert result["student_ids"] == ["S001", "S002", "S003"]
    assert result["lesson_plan"]["lesson_structure"]
    assert result["summary"]["turn_count"] == 5
    assert len(result["phase_summary"]) == 5

    output_path = export_teaching_strategy_summary(
        result,
        output_path=tmp_path / "summary.txt",
    )
    assert output_path.exists()
    assert "Teaching Strategy Experiment Result Summary" in output_path.read_text(encoding="utf-8")
