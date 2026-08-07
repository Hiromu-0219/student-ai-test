from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from src.teacher import RuleBasedLectureDesignAI


DEFAULT_CURRICULUM_PATH = Path("data/curriculum/linear_equation.json")
SCENARIO_NAMES = [
    "low_understanding_class",
    "wide_gap_class",
    "high_understanding_class",
    "common_misconception_class",
]


def run_lesson_design_validity_evaluation(
    *,
    curriculum_path: str | Path = DEFAULT_CURRICULUM_PATH,
    total_minutes: int = 30,
) -> dict[str, Any]:
    curriculum = _load_curriculum(curriculum_path)
    designer = RuleBasedLectureDesignAI()
    scenarios = _scenario_teacher_beliefs()
    scenario_results = []
    for scenario_name in SCENARIO_NAMES:
        teacher_beliefs = scenarios[scenario_name]
        design = designer.design_lecture(
            teacher_beliefs=teacher_beliefs,
            curriculum=curriculum,
            total_minutes=total_minutes,
            lecture_id=f"lecture_design_validity_{scenario_name}",
        )
        scenario_results.append(
            {
                "scenario": scenario_name,
                "input_summary": _belief_summary(teacher_beliefs),
                "design": design,
                "design_summary": _design_summary(design),
            }
        )

    comparison_rows = _comparison_rows(scenario_results)
    validity_checks = _validity_checks(scenario_results, comparison_rows, total_minutes)
    return {
        "experiment": "lesson_design_validity",
        "total_minutes": total_minutes,
        "scenario_results": scenario_results,
        "comparison_rows": comparison_rows,
        "validity_checks": validity_checks,
        "summary": _summary(validity_checks, comparison_rows),
    }


def export_lesson_design_validity_for_codex(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/lesson_design_validity_for_codex.txt",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Lesson Design Validity Evaluation For Codex",
        "",
        "このファイルをCodex/ChatGPTに渡すときは、このtxtをそのまま添付してください。",
        "",
        "## Purpose",
        "授業設計AIが、伝達AIから教師側に渡された推定情報だけを入力として、クラス条件に応じた講義構成を提案できるかを検証します。",
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
            "## Scenario Comparison",
            (
                "scenario\tavg_score\tscore_std\tlow_count\thigh_count\tgoal\tpace\t"
                "whole_explanation_min\tpractice_min\tcheck_min\toptimization_targets\trisk_count"
            ),
        ]
    )
    for row in result.get("comparison_rows", []):
        lines.append(
            "\t".join(
                [
                    row["scenario"],
                    str(row["avg_score"]),
                    str(row["score_std"]),
                    str(row["low_count"]),
                    str(row["high_count"]),
                    row["goal"],
                    row["pace"],
                    str(row["whole_explanation_min"]),
                    str(row["practice_min"]),
                    str(row["check_min"]),
                    ",".join(row["optimization_targets"]),
                    str(row["risk_count"]),
                ]
            )
        )

    lines.extend(["", "## Scenario Details"])
    for item in result.get("scenario_results", []):
        lines.extend(
            [
                f"### {item['scenario']}",
                "input_summary:",
                json.dumps(item["input_summary"], ensure_ascii=False, indent=2),
                "design_summary:",
                json.dumps(item["design_summary"], ensure_ascii=False, indent=2),
                "reason:",
                item["design"].get("reason", ""),
                "",
            ]
        )

    lines.extend(
        [
            "## Claim Scope",
            "この実験で主張できるのは、授業設計AIが観察由来のクラス要約に反応して講義構成を変えられることです。実際の授業効果や人間教師より優れていることは、この実験だけでは主張しません。",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _load_curriculum(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _scenario_teacher_beliefs() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "low_understanding_class": {
            f"L{i:02d}": _belief(
                score,
                self_efficacy="low" if i <= 4 else "medium",
                question_tendency="low" if i % 2 == 0 else "medium",
                motivation="medium",
                neuroticism="high" if i <= 3 else "medium",
            )
            for i, score in enumerate([22, 28, 33, 36, 40, 41, 43, 44, 46, 48], start=1)
        },
        "wide_gap_class": {
            f"G{i:02d}": _belief(
                score,
                self_efficacy="low" if score < 45 else "high" if score >= 75 else "medium",
                question_tendency="low" if i in {1, 2, 3, 9} else "medium",
                motivation="low" if score < 35 else "high" if score >= 75 else "medium",
                neuroticism="high" if score < 45 else "low" if score >= 75 else "medium",
            )
            for i, score in enumerate([25, 35, 42, 52, 60, 66, 73, 82, 88, 94], start=1)
        },
        "high_understanding_class": {
            f"H{i:02d}": _belief(
                score,
                self_efficacy="high" if score >= 75 else "medium",
                question_tendency="medium",
                motivation="high",
                neuroticism="low" if score >= 80 else "medium",
            )
            for i, score in enumerate([66, 70, 72, 75, 78, 82, 85, 88, 90, 94], start=1)
        },
        "common_misconception_class": {
            f"M{i:02d}": _belief(
                score,
                self_efficacy="medium",
                question_tendency="low" if i in {2, 5, 8} else "medium",
                motivation="medium",
                neuroticism="medium",
                misconceptions=[
                    {
                        "name": "係数で割る操作に誤概念がある可能性",
                        "confidence": 0.75,
                        "evidence_count": 2,
                    }
                ] if i <= 6 else [],
            )
            for i, score in enumerate([48, 52, 55, 58, 60, 62, 64, 68, 70, 74], start=1)
        },
    }


def _belief(
    score: int,
    *,
    self_efficacy: str = "medium",
    question_tendency: str = "medium",
    motivation: str = "medium",
    neuroticism: str = "medium",
    misconceptions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "estimated_knowledge": {
            "linear_equation": {
                "score": score,
                "confidence": 0.7,
            }
        },
        "estimated_traits": {
            "self_efficacy": {"level": self_efficacy, "confidence": 0.7},
            "question_tendency": {"level": question_tendency, "confidence": 0.7},
            "motivation": {"level": motivation, "confidence": 0.7},
            "conscientiousness": {"level": "medium", "confidence": 0.6},
            "neuroticism": {"level": neuroticism, "confidence": 0.7},
        },
        "estimated_misconceptions": misconceptions or [],
        "evidence_history": ["observable classroom estimate"],
    }


def _belief_summary(teacher_beliefs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scores = [_score(belief) for belief in teacher_beliefs.values()]
    low_count = sum(1 for score in scores if score < 45)
    high_count = sum(1 for score in scores if score >= 65)
    return {
        "student_count": len(teacher_beliefs),
        "avg_score": round(mean(scores), 1),
        "score_std": _pstdev(scores),
        "low_count": low_count,
        "high_count": high_count,
        "trait_counts": _trait_counts(teacher_beliefs),
        "misconception_student_count": sum(
            1 for belief in teacher_beliefs.values() if belief.get("estimated_misconceptions")
        ),
    }


def _design_summary(design: dict[str, Any]) -> dict[str, Any]:
    lecture = design["recommended_lecture"]
    structure = lecture["lesson_structure"]
    return {
        "lesson_goal": lecture["lesson_goal"],
        "whole_class_policy": lecture["whole_class_policy"],
        "optimization_targets": design["optimization_targets"],
        "minutes_by_phase": {phase["phase"]: phase["minutes"] for phase in structure},
        "individual_support_policy_counts": _support_policy_counts(
            lecture["individual_support_policy"]
        ),
        "observable_input_policy": design["observable_input_policy"],
    }


def _comparison_rows(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in scenario_results:
        summary = item["input_summary"]
        design_summary = item["design_summary"]
        minutes = design_summary["minutes_by_phase"]
        rows.append(
            {
                "scenario": item["scenario"],
                "avg_score": summary["avg_score"],
                "score_std": summary["score_std"],
                "low_count": summary["low_count"],
                "high_count": summary["high_count"],
                "goal": design_summary["lesson_goal"].get("target_skill"),
                "pace": design_summary["whole_class_policy"].get("pace"),
                "whole_explanation_min": minutes.get("全体説明", 0),
                "practice_min": minutes.get("個別演習", 0),
                "check_min": minutes.get("確認", 0),
                "optimization_targets": design_summary["optimization_targets"],
                "risk_count": len(item["design"].get("class_diagnosis", {}).get("common_risks", [])),
            }
        )
    return rows


def _validity_checks(
    scenario_results: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    total_minutes: int,
) -> list[dict[str, Any]]:
    rows_by_name = {row["scenario"]: row for row in comparison_rows}
    designs_by_name = {item["scenario"]: item["design"] for item in scenario_results}

    input_policy_ok = all(
        "true_student_knowledge_state" in design["observable_input_policy"]["does_not_use"]
        and "raw_hidden_student_parameters" in design["observable_input_policy"]["does_not_use"]
        for design in designs_by_name.values()
    )
    goal_set = {row["goal"] for row in comparison_rows}
    pace_set = {row["pace"] for row in comparison_rows}
    minutes_ok = all(
        sum(phase["minutes"] for phase in item["design"]["recommended_lecture"]["lesson_structure"])
        == total_minutes
        for item in scenario_results
    )

    low = rows_by_name["low_understanding_class"]
    gap = rows_by_name["wide_gap_class"]
    high = rows_by_name["high_understanding_class"]
    misconception = rows_by_name["common_misconception_class"]

    return [
        _check(
            "observable_input_policy",
            input_policy_ok,
            1.0 if input_policy_ok else 0.0,
            "授業設計AIがtrue stateではなくteacher_beliefs由来の推定情報を使う設計になっている。",
        ),
        _check(
            "goal_adaptation",
            len(goal_set) >= 2
            and low["goal"] == "can_transpose_terms"
            and high["goal"] == "can_divide_by_coefficient"
            and misconception["goal"] == "can_divide_by_coefficient",
            min(1.0, len(goal_set) / 2),
            "scenarioごとのgoal=" + json.dumps({row["scenario"]: row["goal"] for row in comparison_rows}, ensure_ascii=False),
        ),
        _check(
            "time_allocation_adaptation",
            low["whole_explanation_min"] > high["whole_explanation_min"]
            and gap["practice_min"] >= high["practice_min"]
            and len(pace_set) >= 3
            and minutes_ok,
            1.0 if minutes_ok and len(pace_set) >= 3 else 0.5,
            "低理解クラスは説明を厚く、学力差クラスは個別演習を厚く、高理解クラスは標準ペースにする。",
        ),
        _check(
            "whole_class_optimization_targets",
            "reduce_between_student_gap" in gap["optimization_targets"]
            and "support_low_estimated_understanding_students" in low["optimization_targets"]
            and "address_common_misconceptions" in misconception["optimization_targets"],
            1.0,
            "クラス全体のリスクに応じたoptimization_targetsが出るかを見る。",
        ),
        _check(
            "individual_support_policy_presence",
            all(
                item["design"]["recommended_lecture"].get("individual_support_policy")
                for item in scenario_results
            ),
            1.0,
            "全体講義だけでなく、個別演習中の支援方針も併せて出す。",
        ),
    ]


def _summary(checks: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed_count = sum(1 for check in checks if check["passed"])
    return {
        "lesson_design_validity_score": round(passed_count / len(checks), 3) if checks else 0,
        "passed_checks": passed_count,
        "total_checks": len(checks),
        "scenario_count": len(rows),
        "distinct_goals": sorted({row["goal"] for row in rows}),
        "distinct_paces": sorted({row["pace"] for row in rows}),
        "verdict": "usable_as_lesson_design_layer" if passed_count == len(checks) else "needs_lesson_design_improvement",
    }


def _score(belief: dict[str, Any]) -> int:
    return int(belief["estimated_knowledge"]["linear_equation"]["score"])


def _trait_counts(teacher_beliefs: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    keys = ["self_efficacy", "question_tendency", "motivation", "neuroticism"]
    counts = {key: {"low": 0, "medium": 0, "high": 0} for key in keys}
    for belief in teacher_beliefs.values():
        traits = belief.get("estimated_traits", {})
        for key in keys:
            level = str(traits.get(key, {}).get("level", "medium"))
            if level in counts[key]:
                counts[key][level] += 1
    return counts


def _support_policy_counts(policies: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for policy in policies:
        label = policy.get("policy", "")
        counts[label] = counts.get(label, 0) + 1
    return counts


def _pstdev(values: list[int]) -> float:
    if len(values) <= 1:
        return 0.0
    average = mean(values)
    return round((sum((value - average) ** 2 for value in values) / len(values)) ** 0.5, 1)


def _check(criterion: str, passed: bool, score: float, reason: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "passed": bool(passed),
        "score": round(float(score), 3),
        "reason": reason,
    }

