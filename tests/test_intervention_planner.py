from src.teacher import RuleBasedInterventionPlanner


def _belief(score=50, self_efficacy="medium", neuroticism="medium", misconceptions=None):
    return {
        "estimated_knowledge": {
            "linear_equation": {"score": score, "confidence": 0.5},
        },
        "estimated_traits": {
            "self_efficacy": {"level": self_efficacy, "confidence": 0.6},
            "question_tendency": {"level": "medium", "confidence": 0.4},
            "motivation": {"level": "medium", "confidence": 0.4},
            "conscientiousness": {"level": "medium", "confidence": 0.4},
            "neuroticism": {"level": neuroticism, "confidence": 0.6},
        },
        "estimated_misconceptions": misconceptions or [],
    }


def test_intervention_planner_separates_whole_class_and_individual_support():
    planner = RuleBasedInterventionPlanner()
    result = planner.plan(
        classroom_observation={
            "student_count": 3,
            "classroom_summary": "3 students observed.",
        },
        teacher_beliefs={
            "S001": _belief(score=40),
            "S002": _belief(score=42, self_efficacy="low"),
            "S003": _belief(score=68),
        },
        lesson_goal={
            "target_skill": "can_transpose_terms",
            "goal_text": "移項すると符号が変わることを理解する",
        },
        recent_events=[
            {"student_id": "S001", "is_correct": False},
            {"student_id": "S002", "is_correct": False},
            {"student_id": "S003", "is_correct": True},
        ],
        next_problem_bank={
            "can_transpose_terms": [{"problem": "x + 3 = 8", "answer": "x = 5"}],
        },
    )

    assert result["whole_class_plan"]["pace"] == "slow_down"
    assert result["whole_class_plan"]["next_problem"] == "x + 3 = 8"
    assert result["individual_supports"]
    support_types = {item["support_type"] for item in result["individual_supports"]}
    assert "confidence_support" in support_types
    assert "micro_practice" in support_types


def test_intervention_planner_gives_extension_when_student_is_ready():
    planner = RuleBasedInterventionPlanner()
    result = planner.plan(
        classroom_observation={"student_count": 3, "classroom_summary": ""},
        teacher_beliefs={
            "S001": _belief(score=70),
            "S002": _belief(score=72),
            "S003": _belief(score=74),
        },
        lesson_goal={"target_skill": "can_solve_ax_plus_b_equals_c"},
        recent_events=[
            {"student_id": "S001", "is_correct": True},
            {"student_id": "S002", "is_correct": True},
            {"student_id": "S003", "is_correct": True},
        ],
        next_problem_bank={
            "can_solve_ax_plus_b_equals_c": [{"problem": "2x + 3 = 11", "answer": "x = 4"}],
        },
    )

    assert result["whole_class_plan"]["pace"] == "maintain_or_raise"
    assert all(item["support_type"] == "extension" for item in result["individual_supports"])
