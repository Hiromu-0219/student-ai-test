from __future__ import annotations

import copy
import json
from pathlib import Path
from statistics import mean
from typing import Any

from src.cognitive_model import CognitiveModel
from src.personality_model import build_personality_profile
from src.state_manager import StateManager
from src.student_ai import StudentAISimulator
from src.test_bank import TestBank


DEFAULT_UNDERSTANDING_LEVELS = list(range(0, 101, 10))


def run_student_ai_evaluation(
    *,
    student_id: str = "S001",
    test_id: str = "linear_equation_20q_001",
    understanding_levels: list[int] | None = None,
    students_dir: str | Path = "data/students",
    tests_dir: str | Path = "data/tests",
    logs_dir: str | Path = "data/logs",
    use_mock_model: bool = True,
) -> dict[str, Any]:
    """Run a richer student-AI-only evaluation.

    This does not update saved student state. It evaluates the cognitive control
    model and speech-style control from copied student states.
    """

    state_manager = StateManager(students_dir)
    base_state = state_manager.load_student(student_id)
    test_data = TestBank(tests_dir).load_test(test_id)
    cognitive_model = CognitiveModel()
    simulator = StudentAISimulator(
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        use_mock_model=use_mock_model,
    )
    levels = understanding_levels or DEFAULT_UNDERSTANDING_LEVELS

    learning_curve = [
        _evaluate_at_understanding(
            base_state=base_state,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
        )
        for score in levels
    ]
    misconception_comparison = _evaluate_misconception_effect(
        base_state=base_state,
        test_data=test_data,
        cognitive_model=cognitive_model,
    )
    skill_breakdown = _evaluate_skill_breakdown(
        base_state=base_state,
        test_data=test_data,
        cognitive_model=cognitive_model,
    )
    utterance_samples = _generate_personality_utterance_samples(
        simulator=simulator,
        base_state=base_state,
    )

    return {
        "student_id": student_id,
        "test_id": test_id,
        "question_count": len(test_data["questions"]),
        "learning_curve": learning_curve,
        "misconception_comparison": misconception_comparison,
        "skill_breakdown": skill_breakdown,
        "utterance_samples": utterance_samples,
        "summary": _evaluation_summary(
            learning_curve=learning_curve,
            misconception_comparison=misconception_comparison,
            skill_breakdown=skill_breakdown,
        ),
    }


def export_student_ai_evaluation(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/student_ai_evaluation_summary.txt",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Student AI Evaluation Summary",
        "",
        "## Summary",
        json.dumps(result["summary"], ensure_ascii=False, indent=2),
        "",
        "## Learning Curve",
    ]
    lines.extend(json.dumps(row, ensure_ascii=False) for row in result["learning_curve"])
    lines.extend(
        [
            "",
            "## Misconception Comparison",
            json.dumps(result["misconception_comparison"], ensure_ascii=False, indent=2),
            "",
            "## Skill Breakdown",
        ]
    )
    lines.extend(json.dumps(row, ensure_ascii=False) for row in result["skill_breakdown"])
    lines.extend(
        [
            "",
            "## Utterance Samples",
            json.dumps(result["utterance_samples"], ensure_ascii=False, indent=2),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _evaluate_at_understanding(
    *,
    base_state: dict[str, Any],
    test_data: dict[str, Any],
    cognitive_model: CognitiveModel,
    score: int,
) -> dict[str, Any]:
    state = _state_with_uniform_score(base_state, score)
    directives = [
        cognitive_model.build_assessment_directive(
            student_state=state,
            question=question,
        )
        for question in test_data["questions"]
    ]
    correct_count = sum(1 for directive in directives if directive["target_correct"])
    probabilities = [directive["correct_probability"] for directive in directives]
    return {
        "understanding": score,
        "correct_count": correct_count,
        "total_count": len(directives),
        "accuracy": round(correct_count / len(directives), 3),
        "average_correct_probability": round(mean(probabilities), 1),
    }


def _evaluate_misconception_effect(
    *,
    base_state: dict[str, Any],
    test_data: dict[str, Any],
    cognitive_model: CognitiveModel,
) -> dict[str, Any]:
    rows = []
    for score in [20, 50, 80]:
        with_misconception = _state_with_uniform_score(base_state, score)
        without_misconception = _state_with_uniform_score(base_state, score)
        with_misconception["misconceptions"] = [
            "移項しても符号はそのままだと思っている",
            "3x = 15 で 3 を引けばよいと考える",
        ]
        without_misconception["misconceptions"] = []
        with_row = _evaluate_at_understanding(
            base_state=with_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
        )
        without_row = _evaluate_at_understanding(
            base_state=without_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
        )
        rows.append(
            {
                "understanding": score,
                "accuracy_with_misconception": with_row["accuracy"],
                "accuracy_without_misconception": without_row["accuracy"],
                "probability_with_misconception": with_row["average_correct_probability"],
                "probability_without_misconception": without_row["average_correct_probability"],
            }
        )
    return {"rows": rows}


def _evaluate_skill_breakdown(
    *,
    base_state: dict[str, Any],
    test_data: dict[str, Any],
    cognitive_model: CognitiveModel,
) -> list[dict[str, Any]]:
    skill_rows = []
    skills = sorted({question["skill"] for question in test_data["questions"]})
    for weak_skill in skills:
        state = _state_with_uniform_score(base_state, 75)
        state["knowledge_state"]["linear_equation"][weak_skill] = 25
        questions = [question for question in test_data["questions"] if question["skill"] == weak_skill]
        directives = [
            cognitive_model.build_assessment_directive(
                student_state=state,
                question=question,
            )
            for question in questions
        ]
        correct_count = sum(1 for directive in directives if directive["target_correct"])
        skill_rows.append(
            {
                "weak_skill": weak_skill,
                "question_count": len(questions),
                "correct_count": correct_count,
                "accuracy": round(correct_count / len(questions), 3) if questions else None,
                "average_correct_probability": round(
                    mean(directive["correct_probability"] for directive in directives),
                    1,
                )
                if directives
                else None,
            }
        )
    return skill_rows


def _generate_personality_utterance_samples(
    *,
    simulator: StudentAISimulator,
    base_state: dict[str, Any],
) -> list[dict[str, Any]]:
    profiles = {
        "low_confidence_questioner": {
            "self_efficacy": "low",
            "question_tendency": "high",
            "motivation": "medium",
            "big_five": {"neuroticism": "high", "extraversion": "medium", "conscientiousness": "medium"},
        },
        "diligent_confident": {
            "self_efficacy": "high",
            "question_tendency": "medium",
            "motivation": "high",
            "big_five": {"neuroticism": "low", "extraversion": "medium", "conscientiousness": "high"},
        },
        "quiet_low_motivation": {
            "self_efficacy": "medium",
            "question_tendency": "low",
            "motivation": "low",
            "big_five": {"neuroticism": "medium", "extraversion": "low", "conscientiousness": "low"},
        },
    }
    samples = []
    for profile_id, overrides in profiles.items():
        state = _merge_profile(base_state, overrides)
        prompt_profile = build_personality_profile(state)
        answer = simulator.agent.answer(state, "2x + 3 = 11 を解いてください")
        samples.append(
            {
                "profile_id": profile_id,
                "personality_profile": prompt_profile,
                "utterance": answer,
            }
        )
    return samples


def _evaluation_summary(
    *,
    learning_curve: list[dict[str, Any]],
    misconception_comparison: dict[str, Any],
    skill_breakdown: list[dict[str, Any]],
) -> dict[str, Any]:
    first = learning_curve[0]
    last = learning_curve[-1]
    weakest_skill = min(
        skill_breakdown,
        key=lambda row: row["average_correct_probability"] or 100,
    )
    return {
        "accuracy_gain_from_min_to_max": round(last["accuracy"] - first["accuracy"], 3),
        "probability_gain_from_min_to_max": round(
            last["average_correct_probability"] - first["average_correct_probability"],
            1,
        ),
        "weakest_skill_condition": weakest_skill["weak_skill"],
        "misconception_rows": len(misconception_comparison["rows"]),
    }


def _state_with_uniform_score(base_state: dict[str, Any], score: int) -> dict[str, Any]:
    state = copy.deepcopy(base_state)
    linear = state.setdefault("knowledge_state", {}).setdefault("linear_equation", {})
    linear["score"] = score
    for key in [
        "can_solve_ax_plus_b_equals_c",
        "can_transpose_terms",
        "can_divide_by_coefficient",
        "can_handle_negative_numbers",
        "can_handle_fractions",
    ]:
        linear[key] = score
    return state


def _merge_profile(base_state: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(base_state)
    for key, value in overrides.items():
        if key == "big_five":
            big_five = dict(state.get("big_five", {}))
            big_five.update(value)
            state["big_five"] = big_five
        else:
            state[key] = value
    return state
