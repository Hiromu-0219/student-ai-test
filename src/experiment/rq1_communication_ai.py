from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from src.class_manager import ClassManager
from src.cognitive_model import create_cognitive_model
from src.grader import LinearEquationGrader
from src.observer import CommunicationAI
from src.observer.observation_filter import build_observable_event, events_to_communication_rows
from src.student_ai import StudentAISimulator


DEFAULT_CLASS_ID = "class_10_mixed"
DEFAULT_TEST_PATH = Path("data/tests/linear_equation_20q_001.json")
DEFAULT_SEED = 20260807
COMMUNICATION_METHODS = [
    "stats_baseline",
    "rule_based_communication_ai",
    "enhanced_communication_ai",
]
ABLATION_CONDITIONS = [
    "correctness_only",
    "correctness_answer",
    "correctness_answer_utterance",
    "correctness_answer_response_time",
    "all_observable",
]
TRAIT_KEYS = ["self_efficacy", "question_tendency", "motivation", "neuroticism"]
SKILL_KEYS = [
    "can_solve_ax_plus_b_equals_c",
    "can_transpose_terms",
    "can_divide_by_coefficient",
    "can_handle_negative_numbers",
    "can_handle_fractions",
]
HIDDEN_KEYS = {
    "knowledge_state",
    "understanding",
    "error_tendency",
    "misconceptions",
    "personality",
    "big_five",
    "self_efficacy",
    "question_tendency",
    "motivation",
    "learning_history",
    "correct_probability",
    "target_correct",
}


MISCONCEPTION_DEFINITIONS = {
    "transpose_sign": {
        "name": "移項時の符号変化に誤概念がある可能性",
        "affected_skills": ["can_transpose_terms", "can_solve_ax_plus_b_equals_c"],
        "tokens": ["移項", "符号", "反対側"],
        "recommended_check": "移項すると符号が変わる理由を1問で確認する",
    },
    "divide_by_coefficient": {
        "name": "係数で割る操作に誤概念がある可能性",
        "affected_skills": ["can_divide_by_coefficient", "can_solve_ax_plus_b_equals_c"],
        "tokens": ["係数", "割", "3x", "引く"],
        "recommended_check": "ax=b型で両辺をaで割る操作を確認する",
    },
    "negative_numbers": {
        "name": "負の数の符号処理に誤概念がある可能性",
        "affected_skills": ["can_handle_negative_numbers"],
        "tokens": ["マイナス", "負", "-"],
        "recommended_check": "負の係数で割る問題を追加で確認する",
    },
    "fractions": {
        "name": "分数を含む式変形に誤概念がある可能性",
        "affected_skills": ["can_handle_fractions"],
        "tokens": ["分数", "分母", "/"],
        "recommended_check": "分母を払う操作を確認する",
    },
}


def run_rq1_communication_ai_experiment(
    *,
    class_id: str = DEFAULT_CLASS_ID,
    class_size: int | None = None,
    question_count: int = 8,
    classes_dir: str | Path = "data/classes",
    students_dir: str | Path = "data/students",
    test_path: str | Path = DEFAULT_TEST_PATH,
    cognitive_model_type: str = "bkt_irt",
    seed: int = DEFAULT_SEED,
    communication_methods: list[str] | None = None,
    ablation_conditions: list[str] | None = None,
) -> dict[str, Any]:
    manager = ClassManager(classes_dir=classes_dir, students_dir=students_dir)
    students = manager.load_students(class_id)
    if class_size is not None:
        students = students[:class_size]
    questions = _load_questions(test_path)[:question_count]
    cognitive_model = create_cognitive_model(cognitive_model_type)
    simulator = StudentAISimulator(students_dir=str(students_dir), use_mock_model=True)
    grader = LinearEquationGrader()

    events, ground_truth = _generate_observations(
        students=students,
        questions=questions,
        cognitive_model=cognitive_model,
        simulator=simulator,
        grader=grader,
        seed=seed,
    )
    selected_methods = communication_methods or COMMUNICATION_METHODS
    selected_ablations = ablation_conditions or ABLATION_CONDITIONS

    evaluations = []
    for method in selected_methods:
        for ablation in selected_ablations:
            projected_events = [_project_event(event, ablation) for event in events]
            teacher_beliefs = infer_teacher_beliefs_from_observations(
                projected_events,
                method=method,
                ablation_condition=ablation,
            )
            metrics = evaluate_teacher_beliefs(ground_truth, teacher_beliefs)
            evaluations.append(
                {
                    "method": method,
                    "ablation_condition": ablation,
                    "metrics": metrics,
                    "teacher_beliefs": teacher_beliefs,
                    "failure_examples": _failure_examples(
                        ground_truth,
                        teacher_beliefs,
                        projected_events,
                    ),
                }
            )

    return {
        "experiment": "rq1_communication_ai",
        "research_question": "RQ1: 観察可能な学習ログから、学習者の理解度、弱点スキル、誤概念、行動特徴をどの程度正確に推定できるか。",
        "conditions": {
            "class_id": class_id,
            "student_count": len(students),
            "question_count": len(questions),
            "event_count": len(events),
            "seed": seed,
            "cognitive_model": cognitive_model.model_name,
            "communication_methods": selected_methods,
            "ablation_conditions": selected_ablations,
        },
        "observable_events": events,
        "ground_truth": ground_truth,
        "evaluations": evaluations,
        "comparison_rows": _comparison_rows(evaluations),
        "summary": _summary(evaluations),
        "leakage_check": _leakage_check(events),
    }


def infer_teacher_beliefs_from_observations(
    observable_events: list[dict[str, Any]],
    *,
    method: str,
    ablation_condition: str = "all_observable",
) -> dict[str, dict[str, Any]]:
    grouped = _events_by_student(observable_events)
    if method not in COMMUNICATION_METHODS:
        raise ValueError(f"Unknown communication method: {method}")

    communication_results = {}
    if method in {"rule_based_communication_ai", "enhanced_communication_ai"}:
        rows = events_to_communication_rows(observable_events)
        communication_results = {
            row["student_id"]: row
            for row in CommunicationAI().classify_many(rows)
        }

    beliefs = {}
    for student_id, events in grouped.items():
        communication_result = communication_results.get(student_id, {})
        if method == "stats_baseline":
            belief = _build_stats_baseline_belief(student_id, events, ablation_condition)
        elif method == "rule_based_communication_ai":
            belief = _build_rule_based_belief(
                student_id,
                events,
                communication_result,
                ablation_condition,
            )
        else:
            belief = _build_enhanced_belief(
                student_id,
                events,
                communication_result,
                ablation_condition,
            )
        beliefs[student_id] = belief
    return beliefs


def evaluate_teacher_beliefs(
    ground_truth: dict[str, dict[str, Any]],
    teacher_beliefs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    skill_errors = []
    skill_rows = []
    student_rows = []
    overall_errors = []
    bucket_pairs = []
    trait_rows = []
    misconception_truth = []
    misconception_predictions = []
    confidence_points = []

    for student_id, truth in ground_truth.items():
        belief = teacher_beliefs.get(student_id, _empty_structured_belief(student_id))
        student_skill_errors = []
        for skill in SKILL_KEYS:
            true_value = truth["mastery"].get(skill, 0) / 100
            estimate = belief["estimated_mastery"].get(skill, _probability_estimate(0.5, 0.0, [], []))
            error = abs(true_value - estimate["value"])
            skill_errors.append(error)
            student_skill_errors.append(error)
            skill_rows.append({
                "student_id": student_id,
                "skill": skill,
                "true_value": round(true_value, 3),
                "estimated_value": round(estimate["value"], 3),
                "absolute_error": round(error, 3),
                "observation_count": estimate["observation_count"],
            })
            confidence_points.append((estimate["confidence"], error <= 0.2))

        true_overall = truth["overall_understanding"] / 100
        estimated_overall = belief["estimated_overall_understanding"]["value"]
        overall_error = abs(true_overall - estimated_overall)
        overall_errors.append(overall_error)
        bucket_pairs.append((_bucket(true_overall), _bucket(estimated_overall)))
        confidence_points.append((belief["estimated_overall_understanding"]["confidence"], overall_error <= 0.2))
        student_rows.append({
            "student_id": student_id,
            "skill_mae": round(mean(student_skill_errors), 3),
            "true_overall": round(true_overall, 3),
            "estimated_overall": round(estimated_overall, 3),
            "overall_error": round(overall_error, 3),
            "event_count": len(belief.get("source_event_ids", [])),
        })

        for trait in TRAIT_KEYS:
            true_level = truth["traits"].get(trait, "medium")
            estimate = belief["estimated_traits"].get(trait, _level_estimate("medium", 0.0, [], []))
            correct = true_level == estimate["value"]
            trait_rows.append({
                "student_id": student_id,
                "trait": trait,
                "true_level": true_level,
                "estimated_level": estimate["value"],
                "correct": correct,
                "confidence": estimate["confidence"],
            })
            confidence_points.append((estimate["confidence"], correct))

        true_mis = set(truth["misconception_ids"])
        predicted_mis = {item["misconception_id"] for item in belief.get("estimated_misconceptions", [])}
        misconception_truth.extend((student_id, item) for item in true_mis)
        misconception_predictions.extend((student_id, item) for item in predicted_mis)
        for item in belief.get("estimated_misconceptions", []):
            confidence_points.append((item.get("confidence", 0.0), item["misconception_id"] in true_mis))

    true_set = set(misconception_truth)
    pred_set = set(misconception_predictions)
    tp = len(true_set & pred_set)
    precision = tp / len(pred_set) if pred_set else (1.0 if not true_set else 0.0)
    recall = tp / len(true_set) if true_set else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "skill_mastery": {
            "mae": round(mean(skill_errors), 3) if skill_errors else 0.0,
            "rmse": round(math.sqrt(mean(error ** 2 for error in skill_errors)), 3) if skill_errors else 0.0,
            "skill_errors": _skill_error_summary(skill_rows),
            "student_errors": student_rows,
            "observation_count_error_correlation": _pearson(
                [row["event_count"] for row in student_rows],
                [row["skill_mae"] for row in student_rows],
            ),
        },
        "overall_understanding": {
            "mae": round(mean(overall_errors), 3) if overall_errors else 0.0,
            "rank_correlation": _spearman(
                [row["true_overall"] for row in student_rows],
                [row["estimated_overall"] for row in student_rows],
            ),
            "bucket_accuracy": round(sum(1 for a, b in bucket_pairs if a == b) / len(bucket_pairs), 3) if bucket_pairs else 0.0,
        },
        "misconceptions": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "by_misconception": _misconception_breakdown(true_set, pred_set),
        },
        "traits": {
            "accuracy": round(sum(1 for row in trait_rows if row["correct"]) / len(trait_rows), 3) if trait_rows else 0.0,
            "by_trait": _trait_breakdown(trait_rows),
        },
        "confidence": _confidence_metrics(confidence_points),
    }


def export_rq1_communication_ai_results(
    result: dict[str, Any],
    *,
    output_dir: str | Path = "data/assessments",
    stem: str = "rq1_communication_ai",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    txt_path = output_dir / f"{stem}_for_codex.txt"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    txt_path.write_text(_human_readable_report(result), encoding="utf-8")
    return {"json": str(json_path), "txt": str(txt_path)}


def _generate_observations(*, students, questions, cognitive_model, simulator, grader, seed: int):
    events = []
    ground_truth = {}
    for student_index, student in enumerate(students):
        ground_truth[student["student_id"]] = _ground_truth_label(student)
        for question_index, question in enumerate(questions):
            directive = cognitive_model.build_assessment_directive(student_state=student, question=question)
            directive["mode"] = "lesson_probe"
            utterance = simulator.agent.answer(student, question["problem"], assessment_directive=directive)
            grade = grader.grade(question["answer"], directive["target_answer"])
            event = build_observable_event(
                lesson_id=f"rq1_lesson_{question_index + 1:02d}",
                teacher_id="T_RQ1",
                student_id=student["student_id"],
                teacher_prompt=question["problem"],
                utterance=utterance,
                answer=directive["target_answer"],
                is_correct=grade["is_correct"],
                response_time_sec=_response_time(student, question, student_index, question_index),
                revision_count=_revision_count(student, directive),
                timestamp=f"2026-08-07T00:{question_index:02d}:{student_index:02d}+00:00",
            ).to_dict()
            event.update({
                "event_id": f"EV_{student['student_id']}_{question['question_id']}",
                "question_id": question["question_id"],
                "skill": question["skill"],
                "difficulty": question.get("difficulty", 1),
                "seed": seed,
            })
            events.append(event)
    return events, ground_truth


def _build_stats_baseline_belief(student_id: str, events: list[dict[str, Any]], ablation: str) -> dict[str, Any]:
    mastery = _mastery_from_correctness(events, use_answer=False)
    overall = _overall_from_mastery(mastery)
    source_ids = [event["event_id"] for event in events]
    return {
        "student_id": student_id,
        "method": "stats_baseline",
        "ablation_condition": ablation,
        "estimated_mastery": mastery,
        "estimated_overall_understanding": overall,
        "estimated_misconceptions": [],
        "estimated_traits": {trait: _level_estimate("medium", 0.0, [], source_ids) for trait in TRAIT_KEYS},
        "risks": _risks(mastery, [], {}),
        "information_gaps": _information_gaps(events, mastery, []),
        "recommended_observations": _recommended_observations(events, mastery, []),
        "source_event_ids": source_ids,
    }


def _build_rule_based_belief(student_id: str, events: list[dict[str, Any]], communication_result: dict[str, Any], ablation: str) -> dict[str, Any]:
    use_answer = ablation in {"correctness_answer", "correctness_answer_utterance", "correctness_answer_response_time", "all_observable"}
    mastery = _mastery_from_correctness(events, use_answer=use_answer)
    overall = _overall_from_mastery(mastery)
    source_ids = [event["event_id"] for event in events]
    traits = _traits_from_communication(communication_result, source_ids, include_gaps=False)
    misconceptions = _misconceptions_from_events(events, enhanced=False)
    return {
        "student_id": student_id,
        "method": "rule_based_communication_ai",
        "ablation_condition": ablation,
        "estimated_mastery": mastery,
        "estimated_overall_understanding": overall,
        "estimated_misconceptions": misconceptions,
        "estimated_traits": traits,
        "risks": _risks(mastery, misconceptions, traits),
        "information_gaps": _information_gaps(events, mastery, misconceptions),
        "recommended_observations": _recommended_observations(events, mastery, misconceptions),
        "source_event_ids": source_ids,
    }


def _build_enhanced_belief(student_id: str, events: list[dict[str, Any]], communication_result: dict[str, Any], ablation: str) -> dict[str, Any]:
    mastery = _mastery_from_correctness(events, use_answer=True)
    overall = _overall_from_mastery(mastery)
    source_ids = [event["event_id"] for event in events]
    traits = _traits_from_communication(communication_result, source_ids, include_gaps=True)
    misconceptions = _misconceptions_from_events(events, enhanced=True)
    return {
        "student_id": student_id,
        "method": "enhanced_communication_ai",
        "ablation_condition": ablation,
        "estimated_mastery": mastery,
        "estimated_overall_understanding": overall,
        "estimated_misconceptions": misconceptions,
        "estimated_traits": traits,
        "risks": _risks(mastery, misconceptions, traits),
        "information_gaps": _information_gaps(events, mastery, misconceptions),
        "recommended_observations": _recommended_observations(events, mastery, misconceptions),
        "source_event_ids": source_ids,
    }


def _mastery_from_correctness(events: list[dict[str, Any]], *, use_answer: bool) -> dict[str, dict[str, Any]]:
    by_skill = defaultdict(list)
    for event in events:
        by_skill[event.get("skill", "unknown")].append(event)
    estimates = {}
    for skill in SKILL_KEYS:
        skill_events = by_skill.get(skill, [])
        evidence = [event["event_id"] for event in skill_events if event.get("is_correct") is True]
        counter = [event["event_id"] for event in skill_events if event.get("is_correct") is False]
        if skill_events:
            correct = len(evidence)
            total = len(skill_events)
            value = (correct + 1) / (total + 2)
            if use_answer and any(event.get("showed_work") for event in skill_events):
                value = min(0.95, value + 0.03)
            confidence = min(0.95, total / (total + 3))
        else:
            value = 0.5
            confidence = 0.0
        estimates[skill] = _probability_estimate(value, confidence, evidence, counter)
    return estimates


def _overall_from_mastery(mastery: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = [item["value"] for item in mastery.values()]
    confidences = [item["confidence"] for item in mastery.values()]
    evidence = sorted({event_id for item in mastery.values() for event_id in item["evidence_event_ids"]})
    counter = sorted({event_id for item in mastery.values() for event_id in item["counter_evidence_event_ids"]})
    return _probability_estimate(mean(values) if values else 0.5, mean(confidences) if confidences else 0.0, evidence, counter)


def _traits_from_communication(communication_result: dict[str, Any], source_ids: list[str], *, include_gaps: bool) -> dict[str, dict[str, Any]]:
    trait_estimates = communication_result.get("trait_estimates", {})
    base_confidence = float(communication_result.get("confidence", 0.0))
    traits = {}
    for trait in TRAIT_KEYS:
        level = trait_estimates.get(trait, "medium")
        confidence = base_confidence if level != "medium" or include_gaps else min(base_confidence, 0.35)
        evidence = source_ids if base_confidence else []
        counter = [] if confidence >= 0.5 else source_ids
        traits[trait] = _level_estimate(level, confidence, evidence, counter)
    return traits


def _misconceptions_from_events(events: list[dict[str, Any]], *, enhanced: bool) -> list[dict[str, Any]]:
    candidates = {}
    for event in events:
        if event.get("is_correct") is not False:
            continue
        text = " ".join(str(event.get(key, "")) for key in ["teacher_prompt", "utterance", "answer", "skill"])
        for misconception_id, definition in MISCONCEPTION_DEFINITIONS.items():
            if event.get("skill") in definition["affected_skills"] or any(token in text for token in definition["tokens"]):
                current = candidates.setdefault(misconception_id, {
                    "misconception_id": misconception_id,
                    "name": definition["name"],
                    "confidence": 0.0,
                    "affected_skills": definition["affected_skills"],
                    "evidence_event_ids": [],
                    "counter_evidence_event_ids": [],
                    "recommended_check": definition["recommended_check"] if enhanced else None,
                })
                current["evidence_event_ids"].append(event["event_id"])
    for item in candidates.values():
        item["confidence"] = round(min(0.95, 0.35 + 0.2 * len(item["evidence_event_ids"])), 2)
        affected = set(item["affected_skills"])
        item["counter_evidence_event_ids"] = [
            event["event_id"]
            for event in events
            if event.get("skill") in affected and event.get("is_correct") is True
        ]
    return sorted(candidates.values(), key=lambda item: item["confidence"], reverse=True)


def _project_event(event: dict[str, Any], condition: str) -> dict[str, Any]:
    if condition not in ABLATION_CONDITIONS:
        raise ValueError(f"Unknown ablation condition: {condition}")
    projected = {
        "event_id": event["event_id"],
        "lesson_id": event["lesson_id"],
        "teacher_id": event["teacher_id"],
        "student_id": event["student_id"],
        "teacher_prompt": event["teacher_prompt"],
        "question_id": event["question_id"],
        "skill": event["skill"],
        "difficulty": event["difficulty"],
        "is_correct": event["is_correct"],
        "timestamp": event["timestamp"],
        "seed": event["seed"],
    }
    if condition == "correctness_only":
        projected.update({"utterance": "", "answer": None, "response_time_sec": None})
    elif condition == "correctness_answer":
        projected.update({"utterance": str(event.get("answer") or ""), "answer": event.get("answer"), "response_time_sec": None})
    elif condition == "correctness_answer_utterance":
        projected.update({"utterance": event.get("utterance", ""), "answer": event.get("answer"), "response_time_sec": None})
    elif condition == "correctness_answer_response_time":
        projected.update({"utterance": str(event.get("answer") or ""), "answer": event.get("answer"), "response_time_sec": event.get("response_time_sec")})
    else:
        projected.update({"utterance": event.get("utterance", ""), "answer": event.get("answer"), "response_time_sec": event.get("response_time_sec")})
    text = projected.get("utterance") or ""
    projected["asked_question"] = any(token in text for token in ["?", "？", "ですか", "教えて"])
    projected["showed_work"] = any(token in text for token in ["まず", "両辺", "移項", "係数", "="])
    projected["revision_count"] = event.get("revision_count", 0) if condition == "all_observable" else 0
    projected["no_response"] = not text.strip()
    return projected


def _ground_truth_label(student: dict[str, Any]) -> dict[str, Any]:
    linear = student.get("knowledge_state", {}).get("linear_equation", {})
    return {
        "student_id": student["student_id"],
        "overall_understanding": int(linear.get("score", 0) or 0),
        "mastery": {skill: int(linear.get(skill, linear.get("score", 0)) or 0) for skill in SKILL_KEYS},
        "misconception_ids": _true_misconception_ids(student),
        "traits": {
            "self_efficacy": _compress_level(student.get("self_efficacy")),
            "question_tendency": _compress_level(student.get("question_tendency")),
            "motivation": _compress_level(student.get("motivation")),
            "neuroticism": _compress_level(student.get("big_five", {}).get("neuroticism")),
        },
    }


def _true_misconception_ids(student: dict[str, Any]) -> list[str]:
    text = " ".join(str(item) for item in student.get("misconceptions", []) + student.get("error_tendency", []))
    ids = []
    for misconception_id, definition in MISCONCEPTION_DEFINITIONS.items():
        if any(token in text for token in definition["tokens"]):
            ids.append(misconception_id)
    return sorted(set(ids))


def _failure_examples(ground_truth: dict[str, Any], teacher_beliefs: dict[str, Any], events: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    event_by_id = {event["event_id"]: event for event in events}
    failures = []
    for student_id, truth in ground_truth.items():
        belief = teacher_beliefs.get(student_id)
        if not belief:
            continue
        true_bucket = _bucket(truth["overall_understanding"] / 100)
        estimated_bucket = _bucket(belief["estimated_overall_understanding"]["value"])
        true_mis = set(truth["misconception_ids"])
        estimated_mis = {item["misconception_id"] for item in belief.get("estimated_misconceptions", [])}
        trait_misses = [
            trait for trait in TRAIT_KEYS
            if truth["traits"].get(trait) != belief["estimated_traits"].get(trait, {}).get("value")
        ]
        if true_bucket == estimated_bucket and true_mis == estimated_mis and not trait_misses:
            continue
        evidence_ids = belief.get("source_event_ids", [])[:3]
        failures.append({
            "student_id": student_id,
            "true_state": {"overall_bucket": true_bucket, "misconception_ids": sorted(true_mis), "traits": truth["traits"]},
            "estimated_state": {"overall_bucket": estimated_bucket, "misconception_ids": sorted(estimated_mis), "trait_misses": trait_misses},
            "evidence_events": [event_by_id[event_id] for event_id in evidence_ids if event_id in event_by_id],
            "possible_reason": "観察数が少ない、または発話に内部特徴が明示されていない可能性があります。",
            "recommended_observations": belief.get("recommended_observations", []),
        })
        if len(failures) >= limit:
            break
    return failures


def _comparison_rows(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in evaluations:
        metrics = item["metrics"]
        rows.append({
            "method": item["method"],
            "ablation_condition": item["ablation_condition"],
            "skill_mae": metrics["skill_mastery"]["mae"],
            "skill_rmse": metrics["skill_mastery"]["rmse"],
            "overall_mae": metrics["overall_understanding"]["mae"],
            "overall_bucket_accuracy": metrics["overall_understanding"]["bucket_accuracy"],
            "misconception_f1": metrics["misconceptions"]["f1"],
            "trait_accuracy": metrics["traits"]["accuracy"],
            "brier_score": metrics["confidence"]["brier_score"],
            "ece": metrics["confidence"]["expected_calibration_error"],
        })
    return rows


def _summary(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = _comparison_rows(evaluations)
    best_skill = min(rows, key=lambda row: row["skill_mae"])
    best_trait = max(rows, key=lambda row: row["trait_accuracy"])
    best_mis = max(rows, key=lambda row: row["misconception_f1"])
    return {
        "evaluation_count": len(evaluations),
        "best_skill_mastery_method": best_skill["method"],
        "best_skill_mastery_ablation": best_skill["ablation_condition"],
        "best_skill_mae": best_skill["skill_mae"],
        "best_trait_method": best_trait["method"],
        "best_trait_ablation": best_trait["ablation_condition"],
        "best_trait_accuracy": best_trait["trait_accuracy"],
        "best_misconception_method": best_mis["method"],
        "best_misconception_ablation": best_mis["ablation_condition"],
        "best_misconception_f1": best_mis["misconception_f1"],
    }


def _human_readable_report(result: dict[str, Any]) -> str:
    lines = [
        "# RQ1 Communication AI Experiment For Codex",
        "",
        "このファイルをCodex/ChatGPTに渡すときは、このtxtをそのまま添付してください。",
        "",
        "## Research Question",
        result["research_question"],
        "",
        "## Conditions",
        json.dumps(result["conditions"], ensure_ascii=False, indent=2),
        "",
        "## Leakage Check",
        json.dumps(result["leakage_check"], ensure_ascii=False, indent=2),
        "",
        "## Summary",
        json.dumps(result["summary"], ensure_ascii=False, indent=2),
        "",
        "## Method x Ablation Comparison",
        "method\tablation\tskill_mae\tskill_rmse\toverall_mae\tbucket_acc\tmis_f1\ttrait_acc\tbrier\tece",
    ]
    for row in result["comparison_rows"]:
        lines.append("\t".join([
            row["method"], row["ablation_condition"], str(row["skill_mae"]), str(row["skill_rmse"]),
            str(row["overall_mae"]), str(row["overall_bucket_accuracy"]), str(row["misconception_f1"]),
            str(row["trait_accuracy"]), str(row["brier_score"]), str(row["ece"]),
        ]))
    lines.extend(["", "## Failure Examples"])
    for item in result["evaluations"][:3]:
        lines.append(f"### {item['method']} / {item['ablation_condition']}")
        lines.append(json.dumps(item["failure_examples"][:2], ensure_ascii=False, indent=2))
    return "\n".join(lines).rstrip() + "\n"


def _probability_estimate(value: float, confidence: float, evidence: list[str], counter: list[str]) -> dict[str, Any]:
    return {
        "value": round(max(0.0, min(1.0, value)), 3),
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "evidence_event_ids": sorted(set(evidence)),
        "counter_evidence_event_ids": sorted(set(counter)),
        "observation_count": len(set(evidence) | set(counter)),
    }


def _level_estimate(value: str, confidence: float, evidence: list[str], counter: list[str]) -> dict[str, Any]:
    return {
        "value": value if value in {"low", "medium", "high"} else "medium",
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "evidence_event_ids": sorted(set(evidence)),
        "counter_evidence_event_ids": sorted(set(counter)),
        "observation_count": len(set(evidence) | set(counter)),
    }


def _empty_structured_belief(student_id: str) -> dict[str, Any]:
    return {
        "student_id": student_id,
        "estimated_mastery": {skill: _probability_estimate(0.5, 0.0, [], []) for skill in SKILL_KEYS},
        "estimated_overall_understanding": _probability_estimate(0.5, 0.0, [], []),
        "estimated_misconceptions": [],
        "estimated_traits": {trait: _level_estimate("medium", 0.0, [], []) for trait in TRAIT_KEYS},
        "risks": [],
        "information_gaps": ["観察がありません"],
        "recommended_observations": ["少なくとも1問の回答と発話を観察してください"],
        "source_event_ids": [],
    }


def _information_gaps(events, mastery, misconceptions):
    gaps = []
    if not events:
        return ["観察がありません"]
    observed_skills = {event.get("skill") for event in events}
    missing_skills = [skill for skill in SKILL_KEYS if skill not in observed_skills]
    if missing_skills:
        gaps.append("未観察スキル: " + ",".join(missing_skills))
    if not any(event.get("utterance") for event in events):
        gaps.append("発話情報が不足しています")
    if not misconceptions:
        gaps.append("誤概念を判断する反復的な誤答証拠が不足しています")
    low_confidence = [skill for skill, estimate in mastery.items() if estimate["confidence"] < 0.4]
    if low_confidence:
        gaps.append("習熟度推定の確信度が低いスキル: " + ",".join(low_confidence))
    return gaps


def _recommended_observations(events, mastery, misconceptions):
    recommendations = []
    observed_skills = {event.get("skill") for event in events}
    for skill in SKILL_KEYS:
        if skill not in observed_skills:
            recommendations.append(f"{skill} の問題を追加で観察する")
    if not any(event.get("asked_question") for event in events):
        recommendations.append("質問しやすさを見るため、確認質問を促す場面を作る")
    if not misconceptions:
        recommendations.append("誤概念候補を確認する類題を追加する")
    return recommendations[:5]


def _risks(mastery, misconceptions, traits):
    risks = []
    weak_skills = [skill for skill, estimate in mastery.items() if estimate["value"] < 0.4 and estimate["confidence"] > 0]
    if weak_skills:
        risks.append("低習熟スキル: " + ",".join(weak_skills))
    if misconceptions:
        risks.append("誤概念候補あり")
    if traits.get("self_efficacy", {}).get("value") == "low":
        risks.append("自己効力感が低い可能性")
    if traits.get("question_tendency", {}).get("value") == "low":
        risks.append("質問しにくい可能性")
    return risks


def _skill_error_summary(skill_rows):
    rows = []
    for skill in SKILL_KEYS:
        errors = [row["absolute_error"] for row in skill_rows if row["skill"] == skill]
        rows.append({"skill": skill, "mae": round(mean(errors), 3) if errors else 0.0})
    return rows


def _trait_breakdown(trait_rows):
    rows = []
    for trait in TRAIT_KEYS:
        filtered = [row for row in trait_rows if row["trait"] == trait]
        rows.append({
            "trait": trait,
            "accuracy": round(sum(1 for row in filtered if row["correct"]) / len(filtered), 3) if filtered else 0.0,
        })
    return rows


def _misconception_breakdown(true_set, pred_set):
    rows = []
    for misconception_id in MISCONCEPTION_DEFINITIONS:
        true_items = {item for item in true_set if item[1] == misconception_id}
        pred_items = {item for item in pred_set if item[1] == misconception_id}
        tp = len(true_items & pred_items)
        precision = tp / len(pred_items) if pred_items else (1.0 if not true_items else 0.0)
        recall = tp / len(true_items) if true_items else 1.0
        rows.append({
            "misconception_id": misconception_id,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
        })
    return rows


def _confidence_metrics(points: list[tuple[float, bool]]) -> dict[str, Any]:
    if not points:
        return {"brier_score": 0.0, "expected_calibration_error": 0.0, "bins": []}
    brier = mean((confidence - (1.0 if correct else 0.0)) ** 2 for confidence, correct in points)
    bins = []
    ece = 0.0
    for lower in [0.0, 0.2, 0.4, 0.6, 0.8]:
        upper = lower + 0.2
        bucket = [(conf, ok) for conf, ok in points if lower <= conf < upper or (upper == 1.0 and conf == 1.0)]
        if not bucket:
            continue
        avg_conf = mean(conf for conf, _ in bucket)
        accuracy = mean(1.0 if ok else 0.0 for _, ok in bucket)
        weight = len(bucket) / len(points)
        ece += weight * abs(avg_conf - accuracy)
        bins.append({
            "range": f"{lower:.1f}-{upper:.1f}",
            "count": len(bucket),
            "avg_confidence": round(avg_conf, 3),
            "accuracy": round(accuracy, 3),
        })
    return {"brier_score": round(brier, 3), "expected_calibration_error": round(ece, 3), "bins": bins}


def _leakage_check(events: list[dict[str, Any]]) -> dict[str, Any]:
    leaked_keys = sorted({key for event in events for key in event if key in HIDDEN_KEYS})
    return {"passed": not leaked_keys, "leaked_keys": leaked_keys}


def _events_by_student(events):
    grouped = defaultdict(list)
    for event in events:
        grouped[event["student_id"]].append(event)
    return dict(grouped)


def _load_questions(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def _bucket(value: float) -> str:
    if value < 0.45:
        return "low"
    if value < 0.65:
        return "medium"
    return "high"


def _compress_level(value: Any) -> str:
    if value in {"very_low", "low"}:
        return "low"
    if value in {"very_high", "high"}:
        return "high"
    return "medium"


def _response_time(student, question, student_index, question_index):
    base = 7 + int(question.get("difficulty", 1)) * 2 + (student_index + question_index) % 4
    if _compress_level(student.get("motivation")) == "low":
        base += 4
    if _compress_level(student.get("big_five", {}).get("neuroticism")) == "high":
        base += 3
    return float(base)


def _revision_count(student, directive):
    count = 0
    if _compress_level(student.get("self_efficacy")) == "low":
        count += 1
    if not directive.get("target_correct", True):
        count += 1
    return count


def _pearson(xs, ys):
    if len(xs) < 2 or len(set(xs)) <= 1 or len(set(ys)) <= 1:
        return 0.0
    mx, my = mean(xs), mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round(numerator / denominator, 3) if denominator else 0.0


def _spearman(xs, ys):
    return _pearson(_ranks(xs), _ranks(ys))


def _ranks(values):
    order = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor
        while end + 1 < len(order) and order[end + 1][0] == order[cursor][0]:
            end += 1
        rank = (cursor + end + 2) / 2
        for _, index in order[cursor:end + 1]:
            ranks[index] = rank
        cursor = end + 1
    return ranks
