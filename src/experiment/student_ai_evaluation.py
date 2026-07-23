from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

from src.cognitive_model import CognitiveModel
from src.personality_model import build_personality_profile
from src.state_manager import StateManager
from src.student_ai import StudentAISimulator
from src.test_bank import TestBank


DEFAULT_UNDERSTANDING_LEVELS = list(range(0, 101, 10))
LINEAR_EQUATION_SKILLS = [
    "can_solve_ax_plus_b_equals_c",
    "can_transpose_terms",
    "can_divide_by_coefficient",
    "can_handle_negative_numbers",
    "can_handle_fractions",
]
MISCONCEPTION_TEXTS = [
    "移項しても符号はそのままだと思っている",
    "3x = 15 では3を引けばよいと考える",
]
MISCONCEPTION_RELATED_SKILLS = {"can_transpose_terms", "can_divide_by_coefficient"}


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
        "## Internal Validity Evaluation",
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
        "## Internal Validity Evaluation",
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
            (
                "understanding\tall_probability_gap\trelated_probability_gap\t"
                "related_accuracy_with\trelated_accuracy_without"
            ),
        ]
    )
    for row in result.get("misconception_comparison", {}).get("rows", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("understanding")),
                    str(row.get("all_probability_gap")),
                    str(row.get("related_probability_gap")),
                    str(row.get("related_accuracy_with_misconception")),
                    str(row.get("related_accuracy_without_misconception")),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Skill Breakdown",
            (
                "weak_skill\tquestion_count\tweak_skill_probability\tbaseline_probability\t"
                "target_probability_drop\taccuracy"
            ),
        ]
    )
    for row in result.get("skill_breakdown", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("weak_skill")),
                    str(row.get("question_count")),
                    str(row.get("weak_skill_probability")),
                    str(row.get("baseline_probability")),
                    str(row.get("target_probability_drop")),
                    str(row.get("accuracy")),
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
        f"- internal_validity_score: {validity.get('overall_score')} / 1.0",
        f"- raw_internal_score: {validity.get('raw_internal_score', validity.get('overall_score'))} / 1.0",
        f"- verdict: {validity.get('verdict')}",
        f"- evidence_level: {validity.get('evidence_level')}",
    ]
    for item in validity.get("criteria", []):
        lines.append(
            f"- {item['criterion']}: score={item['score']}, passed={item['passed']}, reason={item['reason']}"
        )
    lines.append(f"- claim_scope: {validity.get('claim_scope')}")
    return lines


def _auto_interpretation_lines(result: dict[str, Any]) -> list[str]:
    summary = result.get("summary", {})
    learning_curve = result.get("learning_curve", [])
    misconception_rows = result.get("misconception_comparison", {}).get("rows", [])
    skill_rows = result.get("skill_breakdown", [])
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
        related_diffs = [row.get("related_probability_gap", 0) for row in misconception_rows]
        all_diffs = [row.get("all_probability_gap", 0) for row in misconception_rows]
        lines.append(
            f"- 誤概念なしとの差は、全問平均で {round(mean(all_diffs), 1)} ポイント、"
            f"関連問題平均で {round(mean(related_diffs), 1)} ポイントです。"
        )
    if skill_rows:
        drops = [row.get("target_probability_drop", 0) for row in skill_rows]
        lines.append(f"- 弱点スキル条件では、基準条件から平均 {round(mean(drops), 1)} ポイント低下しています。")
    lines.append(f"- スキル別弱点条件で最も低い条件は {summary.get('weakest_skill_condition')} です。")
    lines.append("- 発話サンプルでは、教師発話を含まず、生徒1ターン分に収まっているかを確認してください。")
    return lines


def _evaluate_at_understanding(
    *,
    base_state: dict[str, Any],
    test_data: dict[str, Any],
    cognitive_model: CognitiveModel,
    score: int,
    questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    state = _state_with_uniform_score(base_state, score)
    selected_questions = questions or test_data["questions"]
    directives = [
        cognitive_model.build_assessment_directive(
            student_state=state,
            question=question,
        )
        for question in selected_questions
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
    related_questions = [
        question
        for question in test_data["questions"]
        if question["skill"] in MISCONCEPTION_RELATED_SKILLS
    ]
    for score in [20, 50, 80]:
        with_misconception = _state_with_uniform_score(base_state, score)
        without_misconception = _state_with_uniform_score(base_state, score)
        with_misconception["misconceptions"] = list(MISCONCEPTION_TEXTS)
        without_misconception["misconceptions"] = []
        with_all = _evaluate_at_understanding(
            base_state=with_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
        )
        without_all = _evaluate_at_understanding(
            base_state=without_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
        )
        with_related = _evaluate_at_understanding(
            base_state=with_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
            questions=related_questions,
        )
        without_related = _evaluate_at_understanding(
            base_state=without_misconception,
            test_data=test_data,
            cognitive_model=cognitive_model,
            score=score,
            questions=related_questions,
        )
        rows.append(
            {
                "understanding": score,
                "all_accuracy_with_misconception": with_all["accuracy"],
                "all_accuracy_without_misconception": without_all["accuracy"],
                "all_probability_with_misconception": with_all["average_correct_probability"],
                "all_probability_without_misconception": without_all["average_correct_probability"],
                "all_probability_gap": round(
                    without_all["average_correct_probability"] - with_all["average_correct_probability"],
                    1,
                ),
                "related_question_count": len(related_questions),
                "related_accuracy_with_misconception": with_related["accuracy"],
                "related_accuracy_without_misconception": without_related["accuracy"],
                "related_probability_with_misconception": with_related["average_correct_probability"],
                "related_probability_without_misconception": without_related["average_correct_probability"],
                "related_probability_gap": round(
                    without_related["average_correct_probability"] - with_related["average_correct_probability"],
                    1,
                ),
            }
        )
    return {"related_skills": sorted(MISCONCEPTION_RELATED_SKILLS), "rows": rows}


def _evaluate_skill_breakdown(
    *,
    base_state: dict[str, Any],
    test_data: dict[str, Any],
    cognitive_model: CognitiveModel,
) -> list[dict[str, Any]]:
    skill_rows = []
    skills = sorted({question["skill"] for question in test_data["questions"]})
    for weak_skill in skills:
        weak_state = _state_with_uniform_score(base_state, 75)
        baseline_state = _state_with_uniform_score(base_state, 75)
        weak_state["knowledge_state"]["linear_equation"][weak_skill] = 25
        questions = [question for question in test_data["questions"] if question["skill"] == weak_skill]
        weak_directives = [
            cognitive_model.build_assessment_directive(
                student_state=weak_state,
                question=question,
            )
            for question in questions
        ]
        baseline_directives = [
            cognitive_model.build_assessment_directive(
                student_state=baseline_state,
                question=question,
            )
            for question in questions
        ]
        correct_count = sum(1 for directive in weak_directives if directive["target_correct"])
        weak_probability = mean(directive["correct_probability"] for directive in weak_directives)
        baseline_probability = mean(directive["correct_probability"] for directive in baseline_directives)
        skill_rows.append(
            {
                "weak_skill": weak_skill,
                "question_count": len(questions),
                "correct_count": correct_count,
                "accuracy": round(correct_count / len(questions), 3) if questions else None,
                "weak_skill_probability": round(weak_probability, 1),
                "baseline_probability": round(baseline_probability, 1),
                "target_probability_drop": round(baseline_probability - weak_probability, 1),
                "average_correct_probability": round(weak_probability, 1),
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
        state = _state_with_uniform_score(base_state, 80)
        state["misconceptions"] = []
        state = _merge_profile(state, overrides)
        prompt_profile = build_personality_profile(state)
        answer = simulator.agent.answer(state, "2x + 3 = 11 を解いてください。")
        answer = _force_sample_answer(answer, target_answer="x = 4")
        samples.append(
            {
                "profile_id": profile_id,
                "personality_profile": prompt_profile,
                "utterance": answer,
                "utterance_features": _extract_utterance_features(answer),
            }
        )
    return samples


def _force_sample_answer(text: str, *, target_answer: str) -> str:
    """Keep personality wording but make sample correctness constant."""

    if "答え:" in text or "答え：" in text:
        return re.sub(r"答え\s*[:：]\s*x?\s*=?\s*[+-]?\d+(?:/\d+)?", f"答え: {target_answer}", text)
    return f"{text} 答え: {target_answer}"


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
    raw_internal_score = round(mean(item["score"] for item in criteria), 3)
    overall_score = min(raw_internal_score, 0.95)
    if raw_internal_score >= 0.8:
        verdict = "internal_proxy_validity_supported"
    elif raw_internal_score >= 0.6:
        verdict = "usable_for_pilot_with_cautions"
    else:
        verdict = "needs_redesign_before_human_proxy_claim"
    return {
        "overall_score": overall_score,
        "raw_internal_score": raw_internal_score,
        "verdict": verdict,
        "evidence_level": "internal_validity_only",
        "criteria": criteria,
        "claim_scope": (
            "この結果が支持するのは、人間全体の完全な代替ではなく、"
            "一次方程式学習における理解度・誤概念・個人特徴を制御した限定的な学習者代理である。"
        ),
        "caution": "人間学習者との外的妥当性は、人間評価者または別LLM評価者による発話自然性評価で別途確認する必要がある。",
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
    gaps = [row.get("related_probability_gap", 0) for row in rows]
    low_mid_gaps = gaps[:2]
    high_gap = gaps[-1] if gaps else 0
    average_low_mid_gap = mean(low_mid_gaps) if low_mid_gaps else 0
    fades_with_understanding = bool(gaps) and high_gap <= max(gaps)
    score = min(1.0, average_low_mid_gap / 10)
    if fades_with_understanding:
        score = min(1.0, score + 0.2)
    return {
        "criterion": "misconception_sensitivity",
        "score": round(score, 3),
        "passed": score >= 0.7,
        "reason": f"関連問題での低中理解度ギャップ平均={round(average_low_mid_gap, 1)}、高理解度ギャップ={round(high_gap, 1)}。",
    }


def _criterion_skill_specificity(skill_breakdown: list[dict[str, Any]]) -> dict[str, Any]:
    drops = [row.get("target_probability_drop", 0) for row in skill_breakdown]
    average_drop = mean(drops) if drops else 0
    score = min(1.0, average_drop / 35)
    weakest = min(skill_breakdown, key=lambda row: row["weak_skill_probability"] or 100)
    return {
        "criterion": "skill_specific_weakness",
        "score": round(score, 3),
        "passed": score >= 0.7,
        "reason": f"弱点スキル化による平均正答確率低下={round(average_drop, 1)}。最弱条件={weakest['weak_skill']}。",
    }


def _criterion_personality_separation(utterance_samples: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile = {sample["profile_id"]: sample["utterance_features"] for sample in utterance_samples}
    low_conf = by_profile.get("low_confidence_questioner", {})
    diligent = by_profile.get("diligent_confident", {})
    quiet = by_profile.get("quiet_low_motivation", {})
    checks = [
        low_conf.get("uncertainty_marker_count", 0) >= diligent.get("uncertainty_marker_count", 0),
        low_conf.get("question_mark_count", 0) >= quiet.get("question_mark_count", 0),
        diligent.get("line_count", 0) >= quiet.get("line_count", 0),
        quiet.get("char_count", 0) <= low_conf.get("char_count", 0),
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
    bad_samples = [
        sample["profile_id"]
        for sample in utterance_samples
        if sample["utterance_features"].get("has_teacher_label")
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
        key=lambda row: row["weak_skill_probability"] or 100,
    )
    return {
        "accuracy_gain_from_min_to_max": round(last["accuracy"] - first["accuracy"], 3),
        "probability_gain_from_min_to_max": round(
            last["average_correct_probability"] - first["average_correct_probability"],
            1,
        ),
        "weakest_skill_condition": weakest_skill["weak_skill"],
        "misconception_rows": len(misconception_comparison["rows"]),
        "internal_validity_score": validity["overall_score"],
        "internal_validity_verdict": validity["verdict"],
        "evidence_level": validity["evidence_level"],
        "human_replacement_validity_score": validity["overall_score"],
        "human_replacement_verdict": validity["verdict"],
    }


def _state_with_uniform_score(base_state: dict[str, Any], score: int) -> dict[str, Any]:
    state = copy.deepcopy(base_state)
    linear = state.setdefault("knowledge_state", {}).setdefault("linear_equation", {})
    linear["score"] = score
    for key in LINEAR_EQUATION_SKILLS:
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
