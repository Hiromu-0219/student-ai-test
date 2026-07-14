from src.teacher import RuleBasedTeacherUtteranceBuilder


def test_teacher_utterance_builder_renders_whole_class_and_individual_moves():
    plan = {
        "whole_class_plan": {
            "focus": "係数で両辺を割って x を求める",
            "teacher_move": "全体で短い例題を1問扱い、操作を1手ずつ確認する",
            "pace": "slow_down",
            "next_problem": "3x = 15",
            "expected_answer": "x = 5",
        },
        "individual_supports": [
            {
                "student_id": "S002",
                "support_type": "confidence_support",
                "target_skill": "can_divide_by_coefficient",
                "reason": "自己効力感の低さが推定されているため",
            },
            {
                "student_id": "S003",
                "support_type": "extension",
                "target_skill": "can_divide_by_coefficient",
                "reason": "直近正答のため",
            },
        ],
    }

    result = RuleBasedTeacherUtteranceBuilder().build(plan)

    assert "全体で確認" in result["whole_class_utterance"]
    assert "3x = 15" in result["whole_class_utterance"]
    assert result["next_problem"] == "3x = 15"
    assert result["expected_answer"] == "x = 5"
    assert len(result["individual_utterances"]) == 2
    assert result["individual_utterances"][0]["student_id"] == "S002"
    assert "まず1つだけ確認" in result["individual_utterances"][0]["utterance"]


def test_teacher_utterance_builder_handles_empty_individual_supports():
    plan = {
        "whole_class_plan": {
            "focus": "移項すると符号が変わること",
            "teacher_move": "個人で解く時間を取る",
            "pace": "maintain_or_raise",
        },
        "individual_supports": [],
    }

    result = RuleBasedTeacherUtteranceBuilder().build(plan)

    assert "自分で考える時間" in result["whole_class_utterance"]
    assert result["individual_utterances"] == []
