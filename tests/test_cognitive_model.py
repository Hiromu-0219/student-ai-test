from src.cognitive_model import CognitiveModel


def student_state(score):
    return {
        "student_id": f"S{score}",
        "knowledge_state": {
            "linear_equation": {
                "level": "medium",
                "score": score,
                "can_solve_ax_plus_b_equals_c": score,
            }
        },
        "misconceptions": [] if score >= 60 else ["移項しても符号は変えなくてよい"],
        "self_efficacy": "medium",
        "motivation": "medium",
    }


def test_cognitive_model_probability_increases_with_knowledge_score():
    model = CognitiveModel()
    question = {
        "question_id": "Q001",
        "answer": "x = 4",
        "skill": "can_solve_ax_plus_b_equals_c",
    }

    low = model.build_assessment_directive(student_state=student_state(0), question=question)
    high = model.build_assessment_directive(student_state=student_state(100), question=question)

    assert low["correct_probability"] < high["correct_probability"]
    assert low["target_answer"] != high["target_answer"]


def test_cognitive_model_uses_wrong_answer_when_target_incorrect():
    model = CognitiveModel()
    question = {
        "question_id": "Q001",
        "answer": "x = 4",
        "skill": "can_solve_ax_plus_b_equals_c",
    }

    directive = None
    for index in range(100):
        state = student_state(0)
        state["student_id"] = f"LOW_{index}"
        candidate = model.build_assessment_directive(student_state=state, question=question)
        if not candidate["target_correct"]:
            directive = candidate
            break

    assert directive is not None
    assert directive["target_correct"] is False
    assert directive["target_answer"] != "x = 4"


def test_cognitive_model_correctness_is_monotonic_for_same_question():
    model = CognitiveModel()
    question = {
        "question_id": "Q001",
        "answer": "x = 4",
        "skill": "can_solve_ax_plus_b_equals_c",
    }
    directives = [
        model.build_assessment_directive(student_state=student_state(score), question=question)
        for score in [0, 20, 40, 60, 80, 100]
    ]
    probabilities = [directive["correct_probability"] for directive in directives]
    correctness = [directive["target_correct"] for directive in directives]

    assert probabilities == sorted(probabilities)
    assert correctness == sorted(correctness)


def test_misconception_penalty_fades_as_skill_increases():
    model = CognitiveModel()
    question = {
        "question_id": "Q001",
        "answer": "x = 4",
        "skill": "can_transpose_terms",
    }
    low = student_state(20)
    high = student_state(80)
    low["knowledge_state"]["linear_equation"]["can_transpose_terms"] = 20
    high["knowledge_state"]["linear_equation"]["can_transpose_terms"] = 80
    low["misconceptions"] = ["移項しても符号は変えなくてよい"]
    high["misconceptions"] = ["移項しても符号は変えなくてよい"]

    low_directive = model.build_assessment_directive(student_state=low, question=question)
    high_directive = model.build_assessment_directive(student_state=high, question=question)

    assert low_directive["misconception_penalty"] > high_directive["misconception_penalty"]


def test_misconception_strength_disappears_at_high_understanding_even_if_text_remains():
    model = CognitiveModel()
    question = {
        "question_id": "Q001",
        "answer": "x = 4",
        "skill": "can_transpose_terms",
    }
    state = student_state(95)
    state["knowledge_state"]["linear_equation"]["can_transpose_terms"] = 95
    state["misconceptions"] = ["移項は項を反対側へ動かすだけで符号はそのままだと思っている"]

    directive = model.build_assessment_directive(student_state=state, question=question)

    assert directive["misconception_strength"] == "none"
    assert directive["misconception_penalty"] == 0
    assert directive["active_misconceptions"] == []
