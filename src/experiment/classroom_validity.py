from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from src.class_manager import ClassManager
from src.cognitive_model import create_cognitive_model


DEFAULT_CLASS_IDS = ["class_3_basic", "class_10_mixed", "class_20_mixed", "class_30_mixed"]
REPRESENTATIVE_CLASSROOM_QUESTIONS = [
    {
        "question_id": "class_validity_easy_divide",
        "problem": "3x = 15 を解きなさい。",
        "answer": "x = 5",
        "skill": "can_divide_by_coefficient",
        "difficulty": 1,
    },
    {
        "question_id": "class_validity_medium_transpose",
        "problem": "x + 3 = 8 を解きなさい。",
        "answer": "x = 5",
        "skill": "can_transpose_terms",
        "difficulty": 2,
    },
    {
        "question_id": "class_validity_hard_multi_step",
        "problem": "2x + 3 = 11 を解きなさい。",
        "answer": "x = 4",
        "skill": "can_solve_ax_plus_b_equals_c",
        "difficulty": 3,
    },
]


SCORE_BUCKETS = [
    ("very_low", 0, 29),
    ("low", 30, 44),
    ("medium", 45, 64),
    ("high", 65, 84),
    ("very_high", 85, 100),
]
TRAIT_KEYS = ["self_efficacy", "question_tendency", "motivation"]
BIG_FIVE_KEYS = ["neuroticism"]


def run_classroom_validity_evaluation(
    *,
    class_ids: list[str] | None = None,
    classes_dir: str | Path = "data/classes",
    students_dir: str | Path = "data/students",
    cognitive_model_type: str = "bkt_irt",
) -> dict[str, Any]:
    manager = ClassManager(classes_dir=classes_dir, students_dir=students_dir)
    model = create_cognitive_model(cognitive_model_type)
    selected_class_ids = class_ids or DEFAULT_CLASS_IDS
    class_results = [
        _evaluate_class(manager, model, class_id)
        for class_id in selected_class_ids
    ]
    return {
        "cognitive_model": model.model_name,
        "class_ids": selected_class_ids,
        "representative_questions": REPRESENTATIVE_CLASSROOM_QUESTIONS,
        "class_results": class_results,
        "comparison_rows": _comparison_rows(class_results),
        "validity_checks": _validity_checks(class_results),
        "summary": _summary(class_results),
    }


def export_classroom_validity_for_codex(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/classroom_validity_for_codex.txt",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Classroom Validity Evaluation For Codex",
        "",
        "このファイルをCodex/ChatGPTに渡すときは、このtxtをそのまま添付してください。",
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
            "## Class Comparison",
            (
                "class_id\tstudent_count\taverage_score\tscore_std\tlow_count\tmedium_count\t"
                "high_count\tmisconception_count\ttrait_variety\tprobe_accuracy\t"
                "probe_probability\trecommended_use"
            ),
        ]
    )
    for row in result.get("comparison_rows", []):
        lines.append(
            "\t".join(
                [
                    str(row.get("class_id")),
                    str(row.get("student_count")),
                    str(row.get("average_score")),
                    str(row.get("score_std")),
                    str(row.get("low_count")),
                    str(row.get("medium_count")),
                    str(row.get("high_count")),
                    str(row.get("misconception_count")),
                    str(row.get("trait_variety")),
                    str(row.get("probe_accuracy")),
                    str(row.get("probe_probability")),
                    str(row.get("recommended_use")),
                ]
            )
        )

    lines.extend(["", "## Class Details"])
    for item in result.get("class_results", []):
        lines.extend(
            [
                f"### {item['class_id']}",
                json.dumps(
                    {
                        "class_features": item.get("class_features"),
                        "score_buckets": item.get("score_buckets"),
                        "trait_counts": item.get("trait_counts"),
                        "probe_summary": item.get("probe_summary"),
                        "visible_class_risks": item.get("visible_class_risks"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _evaluate_class(manager, model, class_id: str) -> dict[str, Any]:
    class_summary = manager.summarize_class(class_id)
    students = manager.load_students(class_id)
    scores = [_score(student) for student in students]
    probe_rows = _probe_class(students, model)
    return {
        "class_id": class_id,
        "student_count": len(students),
        "student_ids": class_summary["student_ids"],
        "class_features": class_summary["class_features"],
        "average_score": round(mean(scores), 1) if scores else 0,
        "score_std": round(pstdev(scores), 1) if len(scores) > 1 else 0.0,
        "score_buckets": _score_buckets(scores),
        "trait_counts": _trait_counts(students),
        "misconception_count": class_summary["misconception_count"],
        "misconception_students": class_summary["misconception_students"],
        "probe_rows": probe_rows,
        "probe_summary": _probe_summary(probe_rows),
        "visible_class_risks": _visible_class_risks(class_summary, students, scores),
    }


def _probe_class(students: list[dict[str, Any]], model) -> list[dict[str, Any]]:
    rows = []
    for question in REPRESENTATIVE_CLASSROOM_QUESTIONS:
        directives = [
            model.build_assessment_directive(student_state=student, question=question)
            for student in students
        ]
        probabilities = [directive["correct_probability"] for directive in directives]
        correct_count = sum(1 for directive in directives if directive["target_correct"])
        rows.append(
            {
                "question_id": question["question_id"],
                "skill": question["skill"],
                "difficulty": question["difficulty"],
                "student_count": len(students),
                "correct_count": correct_count,
                "accuracy": round(correct_count / len(students), 3) if students else 0,
                "average_correct_probability": round(mean(probabilities), 1) if probabilities else 0,
                "min_correct_probability": min(probabilities) if probabilities else 0,
                "max_correct_probability": max(probabilities) if probabilities else 0,
            }
        )
    return rows


def _probe_summary(probe_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not probe_rows:
        return {"accuracy": 0, "average_correct_probability": 0}
    return {
        "accuracy": round(mean(row["accuracy"] for row in probe_rows), 3),
        "average_correct_probability": round(
            mean(row["average_correct_probability"] for row in probe_rows), 1
        ),
        "hard_item_accuracy": next(
            (row["accuracy"] for row in probe_rows if row["difficulty"] == 3),
            None,
        ),
        "hard_item_probability": next(
            (row["average_correct_probability"] for row in probe_rows if row["difficulty"] == 3),
            None,
        ),
    }


def _comparison_rows(class_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in class_results:
        buckets = item["score_buckets"]
        rows.append(
            {
                "class_id": item["class_id"],
                "student_count": item["student_count"],
                "average_score": item["average_score"],
                "score_std": item["score_std"],
                "low_count": buckets["very_low"] + buckets["low"],
                "medium_count": buckets["medium"],
                "high_count": buckets["high"] + buckets["very_high"],
                "misconception_count": item["misconception_count"],
                "trait_variety": _trait_variety(item["trait_counts"]),
                "probe_accuracy": item["probe_summary"]["accuracy"],
                "probe_probability": item["probe_summary"]["average_correct_probability"],
                "recommended_use": _recommended_use(item),
            }
        )
    return rows


def _validity_checks(class_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sizes = [item["student_count"] for item in class_results]
    larger = [item for item in class_results if item["student_count"] >= 10]
    checks = []
    checks.append(
        _check(
            "class_size_scalability",
            set(sizes) >= {3, 10, 20, 30},
            min(1.0, len(set(sizes) & {3, 10, 20, 30}) / 4),
            f"evaluated class sizes={sizes}",
        )
    )
    bucket_ok = all(
        (item["score_buckets"]["very_low"] + item["score_buckets"]["low"] > 0)
        and item["score_buckets"]["medium"] > 0
        and (item["score_buckets"]["high"] + item["score_buckets"]["very_high"] > 0)
        for item in larger
    )
    checks.append(
        _check(
            "score_distribution_visibility",
            bucket_ok,
            sum(
                1
                for item in larger
                if (item["score_buckets"]["very_low"] + item["score_buckets"]["low"] > 0)
                and item["score_buckets"]["medium"] > 0
                and (item["score_buckets"]["high"] + item["score_buckets"]["very_high"] > 0)
            )
            / max(1, len(larger)),
            "larger classes should contain low, middle, and high score groups",
        )
    )
    trait_ok_count = sum(1 for item in larger if _trait_variety(item["trait_counts"]) >= 6)
    checks.append(
        _check(
            "trait_distribution_visibility",
            trait_ok_count == len(larger),
            trait_ok_count / max(1, len(larger)),
            "larger classes should expose multiple observable trait levels",
        )
    )
    misconception_ok = all(item["misconception_count"] > 0 for item in larger)
    checks.append(
        _check(
            "misconception_presence",
            misconception_ok,
            sum(1 for item in larger if item["misconception_count"] > 0) / max(1, len(larger)),
            "larger classes should include students with misconceptions",
        )
    )
    within_class_spreads = [
        max(row["max_correct_probability"] - row["min_correct_probability"] for row in item["probe_rows"])
        for item in larger
        if item["probe_rows"]
    ]
    average_spread = mean(within_class_spreads) if within_class_spreads else 0
    checks.append(
        _check(
            "probe_response_distribution_visibility",
            average_spread >= 40,
            min(1.0, average_spread / 40),
            f"average within-class probe probability spread={round(average_spread, 1)}",
        )
    )
    return checks


def _summary(class_results: list[dict[str, Any]]) -> dict[str, Any]:
    checks = _validity_checks(class_results)
    score = round(mean(check["score"] for check in checks), 3) if checks else 0
    return {
        "class_count": len(class_results),
        "student_count_range": [
            min(item["student_count"] for item in class_results),
            max(item["student_count"] for item in class_results),
        ],
        "average_validity_score": score,
        "verdict": "classroom_proxy_structure_supported" if score >= 0.8 else "needs_classroom_dataset_revision",
        "passed_checks": sum(1 for check in checks if check["passed"]),
        "total_checks": len(checks),
        "claim_scope": (
            "複数生徒クラスの内部状態分布と代表問題への反応が制御可能であり、"
            "教師AIの授業設計入力として使えるクラス環境かを確認する。"
        ),
    }


def _check(criterion: str, passed: bool, score: float, reason: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "passed": bool(passed),
        "score": round(max(0.0, min(1.0, score)), 3),
        "reason": reason,
    }


def _score(student: dict[str, Any]) -> int:
    value = student.get("knowledge_state", {}).get("linear_equation", {}).get("score", 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _score_buckets(scores: list[int]) -> dict[str, int]:
    buckets = {name: 0 for name, _, _ in SCORE_BUCKETS}
    for score in scores:
        for name, low, high in SCORE_BUCKETS:
            if low <= score <= high:
                buckets[name] += 1
                break
    return buckets


def _trait_counts(students: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts = {key: _empty_trait_counts() for key in TRAIT_KEYS + BIG_FIVE_KEYS}
    for student in students:
        for key in TRAIT_KEYS:
            value = student.get(key)
            if value in counts[key]:
                counts[key][value] += 1
        for key in BIG_FIVE_KEYS:
            value = student.get("big_five", {}).get(key)
            if value in counts[key]:
                counts[key][value] += 1
    return counts


def _empty_trait_counts() -> dict[str, int]:
    return {"very_low": 0, "low": 0, "medium": 0, "high": 0, "very_high": 0}


def _trait_variety(trait_counts: dict[str, dict[str, int]]) -> int:
    return sum(
        1
        for counts in trait_counts.values()
        for count in counts.values()
        if count > 0
    )


def _visible_class_risks(
    class_summary: dict[str, Any],
    students: list[dict[str, Any]],
    scores: list[int],
) -> list[str]:
    risks = []
    if any(score < 45 for score in scores):
        risks.append("低理解層が含まれる")
    if class_summary.get("score_std", 0) >= 15:
        risks.append("理解度のばらつきが大きい")
    if class_summary.get("misconception_count", 0) > 0:
        risks.append("誤概念を持つ生徒が含まれる")
    low_question_count = sum(1 for student in students if student.get("question_tendency") in {"very_low", "low"})
    if low_question_count >= max(2, len(students) // 3):
        risks.append("質問しにくい生徒が多い")
    low_efficacy_count = sum(1 for student in students if student.get("self_efficacy") in {"very_low", "low"})
    if low_efficacy_count >= max(2, len(students) // 4):
        risks.append("自己効力感が低い生徒が複数いる")
    return risks


def _recommended_use(item: dict[str, Any]) -> str:
    size = item["student_count"]
    if size <= 3:
        return "debug_small_flow"
    if size <= 10:
        return "classroom_summary_pilot"
    if size <= 20:
        return "standard_classroom_experiment"
    return "large_classroom_scalability_check"
