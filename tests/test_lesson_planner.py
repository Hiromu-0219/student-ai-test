from src.teacher import RuleBasedLessonPlanner


def _belief(score, self_efficacy="medium", question_tendency="medium", neuroticism="medium"):
    return {
        "estimated_knowledge": {"linear_equation": {"score": score, "confidence": 0.5}},
        "estimated_traits": {
            "self_efficacy": {"level": self_efficacy, "confidence": 0.5},
            "question_tendency": {"level": question_tendency, "confidence": 0.5},
            "motivation": {"level": "medium", "confidence": 0.5},
            "conscientiousness": {"level": "medium", "confidence": 0.5},
            "neuroticism": {"level": neuroticism, "confidence": 0.5},
        },
        "estimated_misconceptions": [],
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


def test_lesson_planner_builds_class_profile():
    profile = RuleBasedLessonPlanner().build_class_profile(
        {
            "S001": _belief(40, self_efficacy="low"),
            "S002": _belief(50, question_tendency="low"),
            "S003": _belief(70),
        }
    )

    assert profile["student_count"] == 3
    assert profile["average_estimated_score"] == 53.3
    assert profile["low_score_students"] == ["S001"]
    assert profile["trait_counts"]["self_efficacy"]["low"] == 1


def test_lesson_planner_creates_whole_lesson_structure():
    plan = RuleBasedLessonPlanner().plan_lesson(
        teacher_beliefs={
            "S001": _belief(38, self_efficacy="low"),
            "S002": _belief(42, question_tendency="low"),
            "S003": _belief(68),
        },
        curriculum=_curriculum(),
        total_minutes=30,
    )

    assert plan["lesson_goal"]["target_skill"] == "can_transpose_terms"
    assert len(plan["lesson_structure"]) == 5
    assert sum(phase["minutes"] for phase in plan["lesson_structure"]) == 30
    assert plan["individual_support_policy"]
    assert "class_profile" in plan


def test_lesson_planner_uses_misconception_to_select_goal():
    belief = _belief(60)
    belief["estimated_misconceptions"] = [
        {
            "name": "係数で割る操作に誤概念がある可能性",
            "confidence": 0.7,
            "evidence_count": 2,
        }
    ]

    plan = RuleBasedLessonPlanner().plan_lesson(
        teacher_beliefs={"S001": belief, "S002": _belief(62), "S003": _belief(64)},
        curriculum=_curriculum(),
    )

    assert plan["lesson_goal"]["target_skill"] == "can_divide_by_coefficient"
