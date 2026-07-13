from src.teacher import TeacherContextBuilder, build_teacher_context


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
        "learning_history": [{"event": "old"}, {"event": "recent"}],
    }


def test_build_teacher_context_selects_lowest_priority_skill():
    context = build_teacher_context(
        student_state=_student_state(),
        recent_student_utterance="符号が変わるか自信がありません。",
        communication_observation={"trait_estimates": {"self_efficacy": "low"}},
    )

    assert context["target_skill"] == "can_transpose_terms"
    assert context["lesson_goal"]["target_skill"] == "can_transpose_terms"
    assert context["student_state_summary"]["learning_history_tail"][-1]["event"] == "recent"
    assert context["constraints"]["max_teacher_utterance_chars"] == 120


def test_context_builder_accepts_explicit_target_skill():
    builder = TeacherContextBuilder()
    context = builder.build_context(
        student_state=_student_state(),
        recent_student_utterance="3x = 15 は3を引きますか。",
        communication_observation={"trait_estimates": {"question_tendency": "high"}},
        target_skill="can_divide_by_coefficient",
        constraints={"max_teacher_utterance_chars": 80},
    )

    assert context["target_skill"] == "can_divide_by_coefficient"
    assert context["constraints"]["max_teacher_utterance_chars"] == 80
