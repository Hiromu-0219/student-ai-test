from src.teacher import RuleBasedTeachingStrategySelector, build_teacher_context


def _student_state():
    return {
        "student_id": "S_TEST",
        "name": "Test Student",
        "understanding": {"linear_equation": "low"},
        "knowledge_state": {
            "linear_equation": {
                "score": 40,
                "can_transpose_terms": 10,
                "can_divide_by_coefficient": 30,
                "can_handle_negative_numbers": 20,
                "can_handle_fractions": 50,
                "can_solve_ax_plus_b_equals_c": 40,
            }
        },
        "error_tendency": ["移項で符号を変え忘れる"],
        "misconceptions": ["移項しても符号はそのままだと思っている"],
        "learning_speed": "low",
        "personality": {},
        "big_five": {
            "openness": "medium",
            "conscientiousness": "low",
            "extraversion": "medium",
            "agreeableness": "high",
            "neuroticism": "high",
        },
        "self_efficacy": "low",
        "question_tendency": "high",
        "motivation": "medium",
        "learning_history": [],
    }


def test_strategy_selector_uses_misconception_and_low_confidence():
    context = build_teacher_context(
        student_state=_student_state(),
        recent_student_utterance="符号が変わるのか自信がありません。",
        communication_observation={
            "trait_estimates": {
                "self_efficacy": "low",
                "question_tendency": "high",
                "neuroticism": "high",
            },
            "recommended_teacher_attention": ["不安を下げる声かけを入れる"],
        },
    )

    decision = RuleBasedTeachingStrategySelector().select_strategy(context)

    assert decision["target_skill"] == "can_transpose_terms"
    assert "encouragement" in decision["selected_strategies"]
    assert "misconception_confrontation" in decision["selected_strategies"]
    assert "符号" in decision["teacher_utterance"]
    assert decision["next_problem"] == "x + 3 = 8"


def test_strategy_selector_adds_answer_check_for_high_score():
    state = _student_state()
    state["knowledge_state"]["linear_equation"]["can_transpose_terms"] = 90
    state["knowledge_state"]["linear_equation"]["can_divide_by_coefficient"] = 90
    state["knowledge_state"]["linear_equation"]["can_handle_negative_numbers"] = 90
    state["knowledge_state"]["linear_equation"]["can_handle_fractions"] = 90
    state["knowledge_state"]["linear_equation"]["can_solve_ax_plus_b_equals_c"] = 90
    state["self_efficacy"] = "high"
    state["big_five"]["neuroticism"] = "low"
    state["big_five"]["conscientiousness"] = "high"
    state["misconceptions"] = []

    context = build_teacher_context(
        student_state=state,
        recent_student_utterance="解けました。",
        communication_observation={"trait_estimates": {"self_efficacy": "high"}},
        target_skill="can_solve_ax_plus_b_equals_c",
    )

    decision = RuleBasedTeachingStrategySelector().select_strategy(context)

    assert "answer_check" in decision["selected_strategies"]
    assert decision["expected_answer"] == "x = 4"
