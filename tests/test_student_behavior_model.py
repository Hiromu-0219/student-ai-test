from src.student_behavior_model import build_student_behavior


def _state(**overrides):
    state = {
        "student_id": "S_TEST",
        "self_efficacy": "medium",
        "question_tendency": "medium",
        "motivation": "medium",
    }
    state.update(overrides)
    return state


def test_behavior_model_does_not_solve_in_introduction():
    behavior = build_student_behavior(
        _state(),
        "今日の目標は係数で両辺を割ることです。まず確認しましょう。",
    )

    assert behavior["phase_type"] == "listen"
    assert behavior["action_type"] == "acknowledge"
    assert behavior["should_solve"] is False
    assert behavior["should_include_answer"] is False


def test_behavior_model_solves_lesson_probe():
    behavior = build_student_behavior(
        _state(),
        "例題です。3x = 15 を解いてください。",
        {
            "mode": "lesson_probe",
            "target_correct": True,
            "target_answer": "x = 5",
        },
    )

    assert behavior["phase_type"] == "solve"
    assert behavior["action_type"] == "solve"
    assert behavior["should_solve"] is True
    assert behavior["should_include_answer"] is True
    assert behavior["target_answer"] == "x = 5"


def test_behavior_model_personality_changes_expression_flags():
    behavior = build_student_behavior(
        _state(self_efficacy="low", question_tendency="high"),
        "全体説明です。係数で割ることを確認します。",
    )

    assert behavior["should_ask_question"] is True
    assert behavior["should_express_uncertainty"] is True
