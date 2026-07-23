from src.teacher import RuleBasedLectureDesignAI


def _belief(score, self_efficacy="medium", question_tendency="medium"):
    return {
        "estimated_knowledge": {"linear_equation": {"score": score, "confidence": 0.5}},
        "estimated_traits": {
            "self_efficacy": {"level": self_efficacy, "confidence": 0.5},
            "question_tendency": {"level": question_tendency, "confidence": 0.5},
            "motivation": {"level": "medium", "confidence": 0.5},
            "conscientiousness": {"level": "medium", "confidence": 0.5},
            "neuroticism": {"level": "medium", "confidence": 0.5},
        },
        "estimated_misconceptions": [],
        "evidence_history": [],
    }


def _curriculum():
    return {
        "lesson_goals": [
            {
                "target_skill": "can_transpose_terms",
                "goal_text": "移項すると符号が変わることを理解する",
            },
            {
                "target_skill": "can_divide_by_coefficient",
                "goal_text": "係数で両辺を割って x を求める",
            },
        ],
        "next_problem_bank": {
            "can_transpose_terms": [{"problem": "x + 3 = 8", "answer": "x = 5"}],
            "can_divide_by_coefficient": [
                {"problem": "3x = 15", "answer": "x = 5"},
                {"problem": "5x = 20", "answer": "x = 4"},
            ],
        },
    }


def test_lecture_design_ai_outputs_whole_class_lecture_proposal():
    design = RuleBasedLectureDesignAI().design_lecture(
        teacher_beliefs={
            "S001": _belief(35, self_efficacy="low"),
            "S002": _belief(42, question_tendency="low"),
            "S003": _belief(70),
        },
        curriculum=_curriculum(),
        total_minutes=30,
        lecture_id="L001",
    )

    assert design["role"] == "lecture_design_ai"
    assert design["lecture_id"] == "L001"
    assert design["objective"] == "optimize_whole_class_lecture_from_observable_estimates"
    assert "true_student_knowledge_state" in design["observable_input_policy"]["does_not_use"]
    assert design["recommended_lecture"]["lesson_structure"]
    assert design["recommended_lecture"]["individual_support_policy"]
    assert design["lesson_plan"]["lesson_goal"] == design["recommended_lecture"]["lesson_goal"]
    assert design["lesson_plan"]["lesson_structure"] == design["recommended_lecture"]["lesson_structure"]


def test_lecture_design_ai_changes_targets_for_mixed_class():
    design = RuleBasedLectureDesignAI().design_lecture(
        teacher_beliefs={
            "S001": _belief(30, question_tendency="low"),
            "S002": _belief(60, question_tendency="low"),
            "S003": _belief(90),
        },
        curriculum=_curriculum(),
        total_minutes=30,
    )

    assert "reduce_between_student_gap" in design["optimization_targets"]
    assert "increase_teacher_initiated_check_questions" in design["optimization_targets"]
    assert design["recommended_lecture"]["whole_class_policy"]["pace"] == "adaptive"
