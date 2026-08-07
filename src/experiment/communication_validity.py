from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from src.class_manager import ClassManager
from src.cognitive_model import create_cognitive_model
from src.grader import LinearEquationGrader
from src.observer import CommunicationAI
from src.observer.observation_filter import build_observable_event, events_to_communication_rows
from src.student_ai import StudentAISimulator


DEFAULT_CLASS_ID = "class_30_mixed"
PROBE_QUESTION = {
    "question_id": "communication_validity_probe",
    "problem": "2x + 3 = 11 を解きなさい。途中で考えたことも一言だけ書いてください。",
    "answer": "x = 4",
    "skill": "can_solve_ax_plus_b_equals_c",
    "difficulty": 3,
}
TRAIT_KEYS = [
    "self_efficacy",
    "question_tendency",
    "motivation",
    "neuroticism",
]
OBSERVABLE_ROW_KEYS = {"student_id", "answer", "observable_event"}


def run_communication_validity_evaluation(
    *,
    class_id: str = DEFAULT_CLASS_ID,
    classes_dir: str | Path = "data/classes",
    students_dir: str | Path = "data/students",
    cognitive_model_type: str = "bkt_irt",
    communication_ai: CommunicationAI | None = None,
) -> dict[str, Any]:
    """Evaluate whether communication AI can infer useful state from observations.

    The communication AI receives only observable lesson data. Hidden student
    parameters are used only after inference, as labels for evaluation.
    """

    manager = ClassManager(classes_dir=classes_dir, students_dir=students_dir)
    students = manager.load_students(class_id)
    cognitive_model = create_cognitive_model(cognitive_model_type)
    simulator = StudentAISimulator(students_dir=str(students_dir), use_mock_model=True)
    grader = LinearEquationGrader()
    observer = communication_ai or CommunicationAI()

    events = []
    hidden_labels = []
    for index, student in enumerate(students):
        directive = cognitive_model.build_assessment_directive(
            student_state=student,
            question=PROBE_QUESTION,
        )
        directive["mode"] = "lesson_probe"
        utterance = simulator.agent.answer(
            student,
            PROBE_QUESTION["problem"],
            assessment_directive=directive,
        )
        grade = grader.grade(PROBE_QUESTION["answer"], directive["target_answer"])
        events.append(
            build_observable_event(
                lesson_id="communication_validity",
                teacher_id="T001",
                student_id=student["student_id"],
                teacher_prompt=PROBE_QUESTION["problem"],
                utterance=utterance,
                answer=directive["target_answer"],
                is_correct=grade["is_correct"],
                response_time_sec=_synthetic_response_time(student, index),
                revision_count=_synthetic_revision_count(student),
            )
        )
        hidden_labels.append(_hidden_label(student, directive))

    communication_rows = events_to_communication_rows(events)
    classroom_summary = observer.summarize_classroom(
        communication_rows,
        min_students=1,
        max_students=max(20, len(communication_rows)),
    ).to_dict()
    individual_results = classroom_summary["individual_results"]

    per_student_rows = _per_student_rows(
        hidden_labels,
        individual_results,
        classroom_summary["priority_students"],
    )
    trait_accuracy = _trait_accuracy(per_student_rows)
    profile_accuracy = _profile_accuracy(per_student_rows)
    count_agreement = _class_count_agreement(hidden_labels, individual_results)
    priority_recall = _priority_recall(hidden_labels, classroom_summary["priority_students"])
    observable_input_check = _observable_input_check(communication_rows)
    validity_checks = _validity_checks(
        trait_accuracy=trait_accuracy,
        profile_accuracy=profile_accuracy,
        count_agreement=count_agreement,
        priority_recall=priority_recall,
        observable_input_check=observable_input_check,
    )

    return {
        "class_id": class_id,
        "cognitive_model": cognitive_model.model_name,
        "probe_question": PROBE_QUESTION,
        "student_count": len(students),
        "observable_rows": communication_rows,
        "classroom_summary": classroom_summary,
        "per_student_comparison": per_student_rows,
        "trait_accuracy": trait_accuracy,
        "profile_accuracy": profile_accuracy,
        "class_count_agreement": count_agreement,
        "priority_recall": priority_recall,
        "validity_checks": validity_checks,
        "summary": _summary(
            validity_checks,
            trait_accuracy,
            profile_accuracy,
            count_agreement,
            priority_recall,
        ),
    }


def export_communication_validity_for_codex(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/communication_validity_for_codex.txt",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Communication AI Validity Evaluation For Codex",
        "",
        "このファイルをCodex/ChatGPTに渡すときは、このtxtをそのまま添付してください。",
        "",
        "## Purpose",
        "伝達AIが、生徒AIの内部パラメータを直接見ず、授業中に観察できる発話・正誤・反応だけから、教師AIに渡す生徒情報をどの程度推定できるかを検証します。",
        "",
        "## Summary",
        json.dumps(result.get("summary", {}), ensure_ascii=False, indent=2),
        "",
        "## Validity Checks",
    ]
    for check in result.get("validity_checks", []):
        lines.append(
            f"- {check['criterion']}: passed={check['passed']}, score={check['score']}, reason={check['reason']}"
        )

    lines.extend(
        [
            "",
            "## Trait Accuracy",
            "trait\texact_match\tcorrect_count\ttotal_count",
        ]
    )
    for trait, row in result.get("trait_accuracy", {}).items():
        lines.append(
            "\t".join(
                [
                    trait,
                    str(row["exact_match"]),
                    str(row["correct_count"]),
                    str(row["total_count"]),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Profile Accuracy",
            json.dumps(result.get("profile_accuracy", {}), ensure_ascii=False, indent=2),
            "",
            "## Class-level Count Agreement",
            "trait\ttrue_counts\testimated_counts\tcount_accuracy",
        ]
    )
    for trait, row in result.get("class_count_agreement", {}).items():
        lines.append(
            "\t".join(
                [
                    trait,
                    json.dumps(row["true_counts"], ensure_ascii=False),
                    json.dumps(row["estimated_counts"], ensure_ascii=False),
                    str(row["count_accuracy"]),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Priority Student Recall",
            json.dumps(result.get("priority_recall", {}), ensure_ascii=False, indent=2),
            "",
            "## Per-student Comparison",
            (
                "student_id\ttrue_profile\testimated_profile\ttrue_self_efficacy\test_self_efficacy\t"
                "true_question_tendency\test_question_tendency\ttrue_motivation\test_motivation\t"
                "true_neuroticism\test_neuroticism\ttrue_priority\testimated_priority\tutterance"
            ),
        ]
    )
    for row in result.get("per_student_comparison", []):
        lines.append(
            "\t".join(
                [
                    row["student_id"],
                    row["true_profile"],
                    row["estimated_profile"],
                    row["true_traits"]["self_efficacy"],
                    row["estimated_traits"]["self_efficacy"],
                    row["true_traits"]["question_tendency"],
                    row["estimated_traits"]["question_tendency"],
                    row["true_traits"]["motivation"],
                    row["estimated_traits"]["motivation"],
                    row["true_traits"]["neuroticism"],
                    row["estimated_traits"]["neuroticism"],
                    str(row["true_priority"]),
                    str(row["estimated_priority"]),
                    row["utterance"].replace("\n", " "),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Claim Scope",
            "この実験で示すのは、伝達AIが観察可能な生徒発話から教育上使える粗い状態推定を行えるかであり、実際の人格や心理状態を正確に診断することではありません。",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _hidden_label(student: dict[str, Any], directive: dict[str, Any]) -> dict[str, Any]:
    traits = {
        "self_efficacy": _compress_level(student.get("self_efficacy")),
        "question_tendency": _compress_level(student.get("question_tendency")),
        "motivation": _compress_level(student.get("motivation")),
        "neuroticism": _compress_level(student.get("big_five", {}).get("neuroticism")),
    }
    score = int(
        student.get("knowledge_state", {})
        .get("linear_equation", {})
        .get("score", 0)
        or 0
    )
    priority_score = _hidden_priority_score(traits, score, bool(directive.get("target_correct", False)))
    true_priority = priority_score > 0
    return {
        "student_id": student["student_id"],
        "true_traits": traits,
        "true_profile": _profile_from_traits(traits),
        "true_priority": true_priority,
        "score": score,
        "target_correct": bool(directive.get("target_correct", False)),
        "correct_probability": directive.get("correct_probability"),
        "priority_score": priority_score,
    }


def _per_student_rows(
    hidden_labels: list[dict[str, Any]],
    individual_results: list[dict[str, Any]],
    priority_students: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hidden_by_id = {row["student_id"]: row for row in hidden_labels}
    estimated_priority_ids = {
        str(row.get("student_id"))
        for row in priority_students
        if row.get("student_id") is not None
    }
    rows = []
    for result in individual_results:
        student_id = result["student_id"]
        hidden = hidden_by_id[student_id]
        estimated_traits = {
            key: result.get("trait_estimates", {}).get(key, "medium")
            for key in TRAIT_KEYS
        }
        rows.append(
            {
                "student_id": student_id,
                "true_profile": hidden["true_profile"],
                "estimated_profile": result.get("profile_prediction"),
                "true_traits": hidden["true_traits"],
                "estimated_traits": estimated_traits,
                "true_priority": hidden["true_priority"],
                "estimated_priority": student_id in estimated_priority_ids,
                "score": hidden["score"],
                "target_correct": hidden["target_correct"],
                "priority_score": hidden["priority_score"],
                "utterance": result.get("answer", ""),
            }
        )
    return rows


def _trait_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accuracy = {}
    for trait in TRAIT_KEYS:
        correct = sum(
            1
            for row in rows
            if row["true_traits"][trait] == row["estimated_traits"].get(trait)
        )
        total = len(rows)
        accuracy[trait] = {
            "exact_match": round(correct / total, 3) if total else 0,
            "correct_count": correct,
            "total_count": total,
        }
    return accuracy


def _profile_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(1 for row in rows if row["true_profile"] == row["estimated_profile"])
    total = len(rows)
    return {
        "exact_match": round(correct / total, 3) if total else 0,
        "correct_count": correct,
        "total_count": total,
    }


def _class_count_agreement(
    hidden_labels: list[dict[str, Any]],
    individual_results: list[dict[str, Any]],
) -> dict[str, Any]:
    agreement = {}
    for trait in TRAIT_KEYS:
        true_counts = _count_levels(row["true_traits"][trait] for row in hidden_labels)
        estimated_counts = _count_levels(
            result.get("trait_estimates", {}).get(trait, "medium")
            for result in individual_results
        )
        absolute_error = sum(
            abs(true_counts[level] - estimated_counts[level])
            for level in ["low", "medium", "high"]
        )
        total = max(1, len(hidden_labels))
        agreement[trait] = {
            "true_counts": true_counts,
            "estimated_counts": estimated_counts,
            "count_accuracy": round(max(0.0, 1.0 - absolute_error / (2 * total)), 3),
        }
    return agreement


def _priority_recall(
    hidden_labels: list[dict[str, Any]],
    priority_students: list[dict[str, Any]],
) -> dict[str, Any]:
    limit = max(1, len(priority_students))
    sorted_hidden = sorted(
        hidden_labels,
        key=lambda row: (row.get("priority_score", 0), row.get("student_id", "")),
        reverse=True,
    )
    true_ids = {
        row["student_id"]
        for row in sorted_hidden[:limit]
        if row.get("priority_score", 0) > 0
    }
    estimated_ids = {
        str(row.get("student_id"))
        for row in priority_students
        if row.get("student_id") is not None
    }
    hit_ids = sorted(true_ids & estimated_ids)
    return {
        "true_priority_students": sorted(true_ids),
        "estimated_priority_students": sorted(estimated_ids),
        "hit_students": hit_ids,
        "recall": round(len(hit_ids) / len(true_ids), 3) if true_ids else 1.0,
        "precision": round(len(hit_ids) / len(estimated_ids), 3) if estimated_ids else 1.0,
        "comparison": f"top_{limit}_hidden_priority_vs_estimated_priority",
    }


def _observable_input_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hidden_tokens = {
        "true_traits",
        "self_efficacy",
        "question_tendency",
        "motivation",
        "big_five",
        "knowledge_state",
        "misconceptions",
        "correct_probability",
    }
    leaked_keys = sorted(
        {
            key
            for row in rows
            for key in row.keys()
            if key not in OBSERVABLE_ROW_KEYS or key in hidden_tokens
        }
    )
    event_leaks = sorted(
        {
            key
            for row in rows
            for key in row.get("observable_event", {}).keys()
            if key in hidden_tokens
        }
    )
    return {
        "passed": not leaked_keys and not event_leaks,
        "leaked_row_keys": leaked_keys,
        "leaked_observable_event_keys": event_leaks,
    }


def _validity_checks(
    *,
    trait_accuracy: dict[str, Any],
    profile_accuracy: dict[str, Any],
    count_agreement: dict[str, Any],
    priority_recall: dict[str, Any],
    observable_input_check: dict[str, Any],
) -> list[dict[str, Any]]:
    mean_trait_accuracy = mean(row["exact_match"] for row in trait_accuracy.values())
    mean_count_accuracy = mean(row["count_accuracy"] for row in count_agreement.values())
    return [
        _check(
            "observable_input_only",
            observable_input_check["passed"],
            1.0 if observable_input_check["passed"] else 0.0,
            f"leaked_row_keys={observable_input_check['leaked_row_keys']}, leaked_event_keys={observable_input_check['leaked_observable_event_keys']}",
        ),
        _check(
            "individual_trait_estimation",
            mean_trait_accuracy >= 0.5,
            round(mean_trait_accuracy, 3),
            "平均trait一致率が0.5以上なら、発話から粗い個人特徴を拾えているとみなす。",
        ),
        _check(
            "profile_estimation",
            profile_accuracy["exact_match"] >= 0.4,
            profile_accuracy["exact_match"],
            "A/B/C/Dの粗い生徒タイプが一定以上一致するかを見る。",
        ),
        _check(
            "class_level_count_agreement",
            mean_count_accuracy >= 0.7,
            round(mean_count_accuracy, 3),
            "クラス全体のlow/medium/high人数分布が大きく崩れていないかを見る。",
        ),
        _check(
            "priority_student_recall",
            priority_recall["recall"] >= 0.4,
            priority_recall["recall"],
            "教師が注意すべき生徒を伝達AIがどれだけ拾えるかを見る。",
        ),
    ]


def _summary(
    checks: list[dict[str, Any]],
    trait_accuracy: dict[str, Any],
    profile_accuracy: dict[str, Any],
    count_agreement: dict[str, Any],
    priority_recall: dict[str, Any],
) -> dict[str, Any]:
    passed_count = sum(1 for check in checks if check["passed"])
    return {
        "communication_validity_score": round(passed_count / len(checks), 3) if checks else 0,
        "passed_checks": passed_count,
        "total_checks": len(checks),
        "mean_trait_accuracy": round(mean(row["exact_match"] for row in trait_accuracy.values()), 3),
        "profile_accuracy": profile_accuracy["exact_match"],
        "mean_class_count_accuracy": round(mean(row["count_accuracy"] for row in count_agreement.values()), 3),
        "priority_recall": priority_recall["recall"],
        "verdict": "usable_as_observation_layer" if passed_count == len(checks) else "needs_observer_improvement",
    }


def _check(criterion: str, passed: bool, score: float, reason: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "passed": bool(passed),
        "score": round(float(score), 3),
        "reason": reason,
    }


def _count_levels(values) -> dict[str, int]:
    counts = {"low": 0, "medium": 0, "high": 0}
    for value in values:
        level = value if value in counts else "medium"
        counts[level] += 1
    return counts


def _compress_level(value: Any) -> str:
    if value in {"very_low", "low"}:
        return "low"
    if value in {"very_high", "high"}:
        return "high"
    return "medium"


def _profile_from_traits(traits: dict[str, str]) -> str:
    if traits["self_efficacy"] == "low" or traits["neuroticism"] == "high":
        return "A"
    if traits["motivation"] == "low" or traits["question_tendency"] == "low":
        return "C"
    if traits["self_efficacy"] == "high" and traits["motivation"] == "high":
        return "D"
    return "B"



def _hidden_priority_score(traits: dict[str, str], score: int, target_correct: bool) -> int:
    priority_score = 0
    if traits["self_efficacy"] == "low":
        priority_score += 3
    if traits["neuroticism"] == "high":
        priority_score += 3
    if traits["motivation"] == "low":
        priority_score += 2
    if traits["question_tendency"] == "low":
        priority_score += 1
    if score < 45:
        priority_score += 2
    if not target_correct:
        priority_score += 2
    return priority_score
def _synthetic_response_time(student: dict[str, Any], index: int) -> float:
    motivation = _compress_level(student.get("motivation"))
    neuroticism = _compress_level(student.get("big_five", {}).get("neuroticism"))
    base = 8.0 + (index % 5)
    if motivation == "low":
        base += 5.0
    if neuroticism == "high":
        base += 3.0
    return round(base, 1)


def _synthetic_revision_count(student: dict[str, Any]) -> int:
    if _compress_level(student.get("self_efficacy")) == "low":
        return 1
    return 0



