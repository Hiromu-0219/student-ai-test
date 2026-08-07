import json

from src.experiment import (
    evaluate_teacher_beliefs,
    infer_teacher_beliefs_from_observations,
    run_rq1_communication_ai_experiment,
)
from src.experiment.rq1_communication_ai import ABLATION_CONDITIONS, HIDDEN_KEYS


def test_rq1_experiment_generates_observable_only_events():
    result = run_rq1_communication_ai_experiment(class_size=3, question_count=4)

    assert result["conditions"]["event_count"] == 12
    assert result["leakage_check"]["passed"] is True
    for event in result["observable_events"]:
        assert not HIDDEN_KEYS & set(event)
        assert "event_id" in event
        assert "student_id" in event


def test_rq1_teacher_belief_json_roundtrip_and_event_ids():
    result = run_rq1_communication_ai_experiment(
        class_size=2,
        question_count=3,
        communication_methods=["enhanced_communication_ai"],
        ablation_conditions=["all_observable"],
    )
    belief = next(iter(result["evaluations"][0]["teacher_beliefs"].values()))

    reloaded = json.loads(json.dumps(belief, ensure_ascii=False))
    assert reloaded == belief
    event_ids = {event["event_id"] for event in result["observable_events"]}
    for estimate in belief["estimated_mastery"].values():
        assert set(estimate["evidence_event_ids"]).issubset(event_ids)
        assert set(estimate["counter_evidence_event_ids"]).issubset(event_ids)


def test_rq1_zero_observation_reports_information_gap():
    beliefs = infer_teacher_beliefs_from_observations([], method="stats_baseline")
    metrics = evaluate_teacher_beliefs(
        {
            "S999": {
                "student_id": "S999",
                "overall_understanding": 50,
                "mastery": {},
                "misconception_ids": [],
                "traits": {},
            }
        },
        beliefs,
    )

    assert beliefs == {}
    assert metrics["skill_mastery"]["mae"] >= 0


def test_rq1_confidence_does_not_drop_when_observations_increase():
    small = run_rq1_communication_ai_experiment(
        class_size=1,
        question_count=2,
        communication_methods=["stats_baseline"],
        ablation_conditions=["correctness_only"],
    )
    large = run_rq1_communication_ai_experiment(
        class_size=1,
        question_count=6,
        communication_methods=["stats_baseline"],
        ablation_conditions=["correctness_only"],
    )
    small_belief = next(iter(small["evaluations"][0]["teacher_beliefs"].values()))
    large_belief = next(iter(large["evaluations"][0]["teacher_beliefs"].values()))

    assert large_belief["estimated_overall_understanding"]["confidence"] >= small_belief["estimated_overall_understanding"]["confidence"]


def test_rq1_metrics_include_misconception_f1_and_skill_mae():
    result = run_rq1_communication_ai_experiment(
        class_size=3,
        question_count=5,
        communication_methods=["stats_baseline", "enhanced_communication_ai"],
        ablation_conditions=["correctness_only", "all_observable"],
    )

    assert len(result["comparison_rows"]) == 4
    for row in result["comparison_rows"]:
        assert 0 <= row["skill_mae"] <= 1
        assert 0 <= row["misconception_f1"] <= 1
        assert 0 <= row["brier_score"] <= 1


def test_rq1_ablation_conditions_are_switchable_and_seed_reproducible():
    first = run_rq1_communication_ai_experiment(
        class_size=2,
        question_count=3,
        seed=123,
        communication_methods=["enhanced_communication_ai"],
        ablation_conditions=ABLATION_CONDITIONS[:2],
    )
    second = run_rq1_communication_ai_experiment(
        class_size=2,
        question_count=3,
        seed=123,
        communication_methods=["enhanced_communication_ai"],
        ablation_conditions=ABLATION_CONDITIONS[:2],
    )

    assert first["comparison_rows"] == second["comparison_rows"]
    assert first["observable_events"] == second["observable_events"]
    assert {row["ablation_condition"] for row in first["comparison_rows"]} == set(ABLATION_CONDITIONS[:2])
