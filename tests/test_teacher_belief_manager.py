from src.observer import build_observable_event
from src.teacher import TeacherBeliefManager


def test_teacher_belief_updates_from_observable_event(tmp_path):
    manager = TeacherBeliefManager(tmp_path)
    event = build_observable_event(
        lesson_id="L001",
        teacher_id="T001",
        student_id="S001",
        teacher_prompt="x + 3 = 8",
        utterance="符号が変わるか不安です。x = 11ですか？",
        answer="x = 11",
        is_correct=False,
        response_time_sec=18.4,
        timestamp="2026-07-13T00:00:00+00:00",
    ).to_dict()
    communication_result = {
        "student_id": "S001",
        "profile_prediction": "A",
        "trait_estimates": {
            "self_efficacy": "low",
            "question_tendency": "high",
            "motivation": "medium",
            "conscientiousness": "medium",
            "neuroticism": "high",
        },
        "confidence": 0.8,
        "evidence": ["不安や迷いの表現がある"],
    }

    belief = manager.update_from_observation(
        teacher_id="T001",
        student_id="S001",
        observable_event=event,
        communication_result=communication_result,
    )

    assert belief["estimated_knowledge"]["linear_equation"]["score"] < 50
    assert belief["estimated_traits"]["self_efficacy"]["level"] == "low"
    assert belief["estimated_traits"]["question_tendency"]["level"] == "high"
    assert belief["estimated_misconceptions"]
    assert belief["evidence_history"]


def test_teacher_belief_update_many_matches_by_student_id(tmp_path):
    manager = TeacherBeliefManager(tmp_path)
    observations = [
        build_observable_event(
            lesson_id="L001",
            teacher_id="T001",
            student_id="S001",
            teacher_prompt="x + 3 = 8",
            utterance="x = 5",
            answer="x = 5",
            is_correct=True,
        ).to_dict(),
        build_observable_event(
            lesson_id="L001",
            teacher_id="T001",
            student_id="S002",
            teacher_prompt="x + 3 = 8",
            utterance="x = 11",
            answer="x = 11",
            is_correct=False,
        ).to_dict(),
    ]
    communication_results = [
        {"student_id": "S001", "trait_estimates": {}, "confidence": 0.5},
        {"student_id": "S002", "trait_estimates": {}, "confidence": 0.5},
    ]

    updated = manager.update_many(
        teacher_id="T001",
        observations=observations,
        communication_results=communication_results,
    )

    assert set(updated) == {"S001", "S002"}
    assert updated["S001"]["estimated_knowledge"]["linear_equation"]["score"] > 50
    assert updated["S002"]["estimated_knowledge"]["linear_equation"]["score"] < 50


def test_teacher_belief_accumulates_confidence_across_lessons(tmp_path):
    manager = TeacherBeliefManager(tmp_path)
    communication_result = {
        "student_id": "S001",
        "profile_prediction": "C",
        "trait_estimates": {
            "self_efficacy": "medium",
            "question_tendency": "low",
            "motivation": "low",
            "conscientiousness": "low",
            "neuroticism": "medium",
        },
        "confidence": 0.7,
        "evidence": ["返答が短い"],
    }

    first_event = build_observable_event(
        lesson_id="L001",
        teacher_id="T001",
        student_id="S001",
        teacher_prompt="x + 3 = 8",
        utterance="x = 5",
        answer="x = 5",
        is_correct=True,
    ).to_dict()
    second_event = build_observable_event(
        lesson_id="L002",
        teacher_id="T001",
        student_id="S001",
        teacher_prompt="2x + 3 = 11",
        utterance="x = 4",
        answer="x = 4",
        is_correct=True,
    ).to_dict()

    first_belief = manager.update_from_observation(
        teacher_id="T001",
        student_id="S001",
        observable_event=first_event,
        communication_result=communication_result,
    )
    second_belief = manager.update_from_observation(
        teacher_id="T001",
        student_id="S001",
        observable_event=second_event,
        communication_result=communication_result,
    )

    first_linear = first_belief["estimated_knowledge"]["linear_equation"]
    second_linear = second_belief["estimated_knowledge"]["linear_equation"]
    assert second_linear["score"] > first_linear["score"]
    assert second_linear["confidence"] > first_linear["confidence"]
    assert len(second_belief["evidence_history"]) == 2
