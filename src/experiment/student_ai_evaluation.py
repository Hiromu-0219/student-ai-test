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
    """Run student-AI-only evaluation without updating saved student state."""

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
    validity = _human_replacement_validity(
        learning_curve=learning_curve,
        misconception_comparison=misconception_comparison,
        skill_breakdown=skill_breakdown,
        utterance_samples=utterance_samples,
    )

    return {
        "student_id": student_id,
        "test_id": test_id,
        "question_count": len(test_data["questions"]),
        "learning_curve": learning_curve,
        "misconception_comparison": misconception_comparison,
        "skill_breakdown": skill_breakdown,
        "utterance_samples": utterance_samples,
        "human_replacement_validity": validity,
        "summary": _evaluation_summary(
            learning_curve=learning_curve,
            misconception_comparison=misconception_comparison,
            skill_breakdown=skill_breakdown,
            validity=validity,
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
        "## Human Replacement Validity",
        json.dumps(result.get("human_replacement_validity", {}), ensure_ascii=False, indent=2),
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


def export_student_ai_evaluation_for_codex(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/student_ai_evaluation_for_codex.txt",
) -> Path:
    """Export a compact txt file that can be attached to this chat."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Student AI Evaluation For Codex",
        "",
        "このファイルをCodex/ChatGPTに渡すときは、このtxtをそのまま添付してください。",
        "",
        "## Basic Info",
        f"student_id: {result.get('student_id')}",
        f"test_id: {result.get('test_id')}",
        f"question_count: {result.get('question_count')}",
        "",
        "## Summary",
        json.dumps(result.get("summary", {}), ensure_ascii=False, indent=2),
        "",
        "## Human Replacement Validity",
        *_validity_lines(result.get("human_replacement_validity", {})),
        "",
        "## Auto Interpretation",
        *_auto_interpretation_lines(result),
        "",
        "## Learning Curve",
        "understanding\tcorrect_count\ttotal_count\taccuracy\taverage_correct_probability",
    ]
    for row in result.get("learning_curve", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("understanding")),
                    str(row.get("correct_count")),
                    str(row.get("total_count")),
                    str(row.get("accuracy")),
                    str(row.get("average_correct_probability")),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Misconception Comparison",
            "understanding\taccuracy_with\taccuracy_without\tprobability_with\tprobability_without\tprobability_gap",
        ]
    )
    for row in result.get("misconception_comparison", {}).get("rows", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("understanding")),
                    str(row.get("accuracy_with_misconception")),
                    str(row.get("accuracy_without_misconception")),
                    str(row.get("probability_with_misconception")),
                    str(row.get("probability_without_misconception")),
                    str(row.get("probability_gap")),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Skill Breakdown",
            "weak_skill\tquestion_count\tcorrect_count\taccuracy\taverage_correct_probability",
        ]
    )
    for row in result.get("skill_breakdown", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("weak_skill")),
                    str(row.get("question_count")),
                    str(row.get("correct_count")),
                    str(row.get("accuracy")),
                    str(row.get("average_correct_probability")),
                ]
            )
        )

    lines.extend(["", "## Utterance Samples"])
    for sample in result.get("utterance_samples", []):
        lines.extend(
            [
                f"profile_id: {sample.get('profile_id')}",
                f"utterance: {sample.get('utterance')}",
                "utterance_features:",
                json.dumps(sample.get("utterance_features", {}), ensure_ascii=False, indent=2),
                "personality_profile:",
                json.dumps(sample.get("personality_profile", {}), ensure_ascii=False, indent=2),
                "",
            ]
        )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _validity_lines(validity: dict[str, Any]) -> list[str]:
    if not validity:
        return ["- human replacement validity result is not available."]
    lines = [
        f"- overall_score: {validity.get('overall_score')} / 1.0",
        f"- verdict: {validity.get('verdict')}",
    ]
    for item in validity.get("criteria", []):
        lines.append(
            f"- {item['criterion']}: score={item['score']}, passed={item['passed']}, reason={item['reason']}"
        )
    return lines


def _auto_interpretation_lines(result: dict[str, Any]) -> list[str]:
    summary = result.get("summary", {})
    learning_curve = result.get("learning_curve", [])
    misconception_rows = result.get("misconception_comparison", {}).get("rows", [])
    lines = []
    gain = summary.get("accuracy_gain_from_min_to_max")
    probability_gain = summary.get("probability_gain_from_min_to_max")
    lines.append(f"- 理解度の上昇により正答率は {gain}、平均正答確率は {probability_gain} ポイント上昇しています。")
    if learning_curve:
        first = learning_curve[0]
        last = learning_curve[-1]
        lines.append(
            f"- 学習曲線は {first.get('understanding')} 点で accuracy={first.get('accuracy')}、"
            f"{last.get('understanding')} 点で accuracy={last.get('accuracy')} です。"
        )
    if misconception_rows:
        diffs = [
            round(row.get("probability_without_misconception", 0) - row.get("probability_with_misconception", 0), 1)
            for row in misconception_rows
        ]
        lines.append(f"- 誤概念なしとの差は平均 {round(mean(diffs), 1)} ポイントです。")
    lines.append(f"- スキル別弱点条件で最も低い条件は {summary.get('weakest_skill_condition')} です。")
    lines.append("- 発話サンプルでは、教師発話を含まず、生徒1ターン分に収まっているかを確認してください。")
    return lines


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
            "3x = 15 では3を引けばよいと考える",
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
                "probability_gap": round(
                    without_row["average_correct_probability"] - with_row["average_correct_probability"],
                    1,
                ),
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
        answer = simulator.agent.answer(state, "2x + 3 = 11 を解いてください。")
        samples.append(
            {
                "profile_id": profile_id,
                "personality_profile": prompt_profile,
                "utterance": answer,
                "utterance_features": _extract_utterance_features(answer),
            }
        )
    return samples


def _human_replacement_validity(
    *,
    learning_curve: list[dict[str, Any]],
    misconception_comparison: dict[str, Any],
    skill_breakdown: list[dict[str, Any]],
    utterance_samples: list[dict[str, Any]],
) -> dict[str, Any]:
    criteria = [
        _criterion_learning_curve(learning_curve),
        _criterion_misconception_effect(misconception_comparison),
        _criterion_skill_specificity(skill_breakdown),
        _criterion_personality_separation(utterance_samples),
        _criterion_one_turn_student_utterance(utterance_samples),
    ]
    overall_score = round(mean(item["score"] for item in criteria), 3)
    if overall_score >= 0.8:
        verdict = "limited_human_proxy_ready"
    elif overall_score >= 0.6:
        verdict = "usable_for_pilot_with_cautions"
    else:
        verdict = "needs_redesign_before_human_proxy_claim"
    return {
        "overall_score": overall_score,
        "verdict": verdict,
        "criteria": criteria,
        "claim_scope": (
            "この結果が支持するのは、人間全体の完全な代替ではなく、"
            "一次方程式学習における理解度・誤概念・個人特徴を制御した限定的な学習者代理である。"
        ),
    }


def _criterion_learning_curve(learning_curve: list[dict[str, Any]]) -> dict[str, Any]:
    probabilities = [row["average_correct_probability"] for row in learning_curve]
    monotonic_pairs = sum(
        1 for before, after in zip(probabilities, probabilities[1:]) if after >= before
    )
    monotonic_rate = monotonic_pairs / max(1, len(probabilities) - 1)
    gain = probabilities[-1] - probabilities[0]
    score = 0.5 * monotonic_rate + 0.5 * min(1.0, max(0.0, gain / 70))
    return {
        "criterion": "cognitive_learning_curve",
        "score": round(score, 3),
        "passed": score >= 0.7,
        "reason": f"理解度上昇に対する平均正答確率の上昇量={round(gain, 1)}、単調性={round(monotonic_rate, 3)}。",
    }


def _criterion_misconception_effect(misconception_comparison: dict[str, Any]) -> dict[str, Any]:
    rows = misconception_comparison.get("rows", [])
    gaps = [row.get("probability_gap", 0) for row in rows]
    low_mid_gaps = gaps[:2]
    high_gap = gaps[-1] if gaps else 0
    average_low_mid_gap = mean(low_mid_gaps) if low_mid_gaps else 0
    fades_with_understanding = bool(gaps) and high_gap <= max(gaps)
    score = min(1.0, average_low_mid_gap / 12)
    if fades_with_understanding:
        score = min(1.0, score + 0.2)
    return {
        "criterion": "misconception_sensitivity",
        "score": round(score, 3),
        "passed": score >= 0.7,
        "reason": f"低中理解度での誤概念ギャップ平均={round(average_low_mid_gap, 1)}、高理解度ギャップ={round(high_gap, 1)}。",
    }


def _criterion_skill_specificity(skill_breakdown: list[dict[str, Any]]) -> dict[str, Any]:
    probabilities = [row["average_correct_probability"] for row in skill_breakdown if row["average_correct_probability"] is not None]
    spread = max(probabilities) - min(probabilities) if probabilities else 0
    score = min(1.0, spread / 20)
    weakest = min(skill_breakdown, key=lambda row: row["average_correct_probability"] or 100)
    return {
        "criterion": "skill_specific_weakness",
        "score": round(score, 3),
        "passed": score >= 0.5,
        "reason": f"スキル条件間の平均正答確率の幅={round(spread, 1)}。最弱条件={weakest['weak_skill']}。",
    }


def _criterion_personality_separation(utterance_samples: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile = {sample["profile_id"]: sample["utterance_features"] for sample in utterance_samples}
    low_conf = by_profile.get("low_confidence_questioner", {})
    diligent = by_profile.get("diligent_confident", {})
    quiet = by_profile.get("quiet_low_motivation", {})
    checks = [
        low_conf.get("question_mark_count", 0) >= diligent.get("question_mark_count", 0),
        low_conf.get("uncertainty_marker_count", 0) > diligent.get("uncertainty_marker_count", 0),
        diligent.get("line_count", 0) >= quiet.get("line_count", 0),
        quiet.get("char_count", 0) <= diligent.get("char_count", 0),
    ]
    score = sum(checks) / len(checks)
    return {
        "criterion": "personality_observable_separation",
        "score": round(score, 3),
        "passed": score >= 0.75,
        "reason": "自信の低さ、質問傾向、丁寧さ、短さが発話特徴として分離しているかを判定。",
    }


def _criterion_one_turn_student_utterance(utterance_samples: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_labels = ["教師:", "先生:", "生徒:", "教師：", "先生：", "生徒："]
    bad_samples = [
        sample["profile_id"]
        for sample in utterance_samples
        if any(label in sample["utterance"] for label in forbidden_labels)
    ]
    score = 1.0 if not bad_samples else 0.0
    return {
        "criterion": "one_turn_student_response",
        "score": score,
        "passed": not bad_samples,
        "reason": "教師発話や話者ラベルを混入させず、生徒1ターンとして観察可能かを判定。",
    }


def _extract_utterance_features(text: str) -> dict[str, Any]:
    uncertainty_markers = ["かな", "かも", "不安", "迷", "わから", "自信", "教えて"]
    return {
        "char_count": len(text),
        "line_count": len([line for line in text.splitlines() if line.strip()]),
        "question_mark_count": text.count("?") + text.count("？"),
        "uncertainty_marker_count": sum(text.count(marker) for marker in uncertainty_markers),
        "has_answer_label": "答え:" in text or "答え：" in text,
        "has_teacher_label": any(label in text for label in ["教師:", "先生:", "教師：", "先生："]),
    }


def _evaluation_summary(
    *,
    learning_curve: list[dict[str, Any]],
    misconception_comparison: dict[str, Any],
    skill_breakdown: list[dict[str, Any]],
    validity: dict[str, Any],
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
        "human_replacement_validity_score": validity["overall_score"],
        "human_replacement_verdict": validity["verdict"],
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
