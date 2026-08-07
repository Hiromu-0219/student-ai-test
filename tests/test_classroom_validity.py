from src.class_manager import ClassManager
from src.experiment import run_classroom_validity_evaluation


def test_repository_30_student_class_loads():
    manager = ClassManager()
    summary = manager.summarize_class("class_30_mixed")

    assert summary["student_count"] == 30
    assert len(summary["student_ids"]) == 30
    assert "S030" in summary["student_ids"]
    assert summary["score_std"] > 0
    assert summary["misconception_count"] > 0


def test_classroom_validity_evaluation_compares_multiple_class_sizes():
    result = run_classroom_validity_evaluation(
        class_ids=["class_3_basic", "class_10_mixed", "class_20_mixed", "class_30_mixed"]
    )

    assert result["summary"]["verdict"] == "classroom_proxy_structure_supported"
    assert result["summary"]["student_count_range"] == [3, 30]
    assert len(result["comparison_rows"]) == 4
    assert {row["student_count"] for row in result["comparison_rows"]} == {3, 10, 20, 30}
    assert all(row["probe_probability"] > 0 for row in result["comparison_rows"])
    assert all(check["passed"] for check in result["validity_checks"])


def test_classroom_validity_contains_visible_distribution_for_large_class():
    result = run_classroom_validity_evaluation(class_ids=["class_30_mixed"])
    class_result = result["class_results"][0]
    buckets = class_result["score_buckets"]

    assert buckets["very_low"] + buckets["low"] > 0
    assert buckets["medium"] > 0
    assert buckets["high"] + buckets["very_high"] > 0
    assert len(class_result["probe_rows"]) == 3
    assert "低理解層が含まれる" in class_result["visible_class_risks"]
