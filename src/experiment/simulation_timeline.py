from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from statistics import mean
from typing import Any

from src.class_manager import ClassManager
from src.config import GenerationConfig, ModelLoadConfig
from src.cognitive_model import create_cognitive_model
from src.experiment.experiment_config import TeachingStrategyExperimentConfig
from src.model_loader import LocalLLM
from src.observer import CommunicationAI, LLMCommunicationAI
from src.student_ai import StudentAISimulator
from src.teacher import LessonSessionRunner, RuleBasedLectureDesignAI
from src.teacher.belief_manager import TeacherBeliefManager


DEFAULT_OUTPUT_DIR = Path("data/assessments")


def run_simulation_timeline(
    *,
    class_id: str = "class_10_mixed",
    cycles: int = 3,
    class_size: int | None = 5,
    total_minutes: int = 30,
    classes_dir: str | Path = "data/classes",
    students_dir: str | Path = "data/students",
    curriculum_path: str | Path = "data/curriculum/linear_equation.json",
    teacher_beliefs_dir: str | Path = "data/teacher_beliefs/simulation_timeline",
    logs_dir: str | Path = "data/logs/simulation_timeline",
    teacher_id: str = "T_SIM",
    use_llm_student: bool = False,
    use_llm_communication: bool = False,
    model_id: str = "Qwen/Qwen3-4B",
    load_in_4bit: bool = True,
    cognitive_model_type: str = "bkt_irt",
    generation_config: GenerationConfig | None = None,
    model_load_config: ModelLoadConfig | None = None,
    update_student_knowledge: bool = False,
    reset_teacher_beliefs: bool = True,
) -> dict[str, Any]:
    """Run a lesson-planning simulation over multiple cycles.

    This is the practical environment for inspecting how the simulation behaves
    over time. Ground truth student states are loaded by the simulator, but the
    communication and teacher layers only receive observable lesson events and
    teacher belief states.
    """

    curriculum = _load_json(curriculum_path)
    if reset_teacher_beliefs:
        _reset_generated_dir(Path(teacher_beliefs_dir))
    class_manager = ClassManager(classes_dir=classes_dir, students_dir=students_dir)
    class_state = class_manager.load_class(class_id)
    student_ids = class_state["student_ids"][:class_size] if class_size else class_state["student_ids"]

    shared_llm = None
    if use_llm_student or use_llm_communication:
        shared_llm = LocalLLM(
            model_id=model_id,
            load_in_4bit=load_in_4bit,
            generation_config=generation_config,
            model_load_config=model_load_config,
        )

    student_simulator = StudentAISimulator(
        use_mock_model=not use_llm_student,
        model_id=model_id,
        students_dir=str(students_dir),
        logs_dir=str(logs_dir),
        generation_config=generation_config,
        model_load_config=model_load_config,
        speech_generator=shared_llm if use_llm_student else None,
    )
    communication_ai = (
        LLMCommunicationAI(shared_llm) if use_llm_communication and shared_llm else CommunicationAI()
    )
    cognitive_model = create_cognitive_model(cognitive_model_type)
    belief_manager = TeacherBeliefManager(teacher_beliefs_dir)
    lecture_designer = RuleBasedLectureDesignAI()

    teacher_beliefs = {
        student_id: belief_manager.load_or_create(teacher_id, student_id)
        for student_id in student_ids
    }
    cycles_result = []
    timeline_rows = []

    for cycle_index in range(1, cycles + 1):
        lecture_design = lecture_designer.design_lecture(
            teacher_beliefs=teacher_beliefs,
            curriculum=curriculum,
            total_minutes=total_minutes,
            lecture_id=f"{class_id}_cycle_{cycle_index:02d}",
        )
        lesson_plan = lecture_design["lesson_plan"]
        session_result = LessonSessionRunner(
            student_simulator=student_simulator,
            communication_ai=communication_ai,
            belief_manager=belief_manager,
            teacher_id=teacher_id,
            update_student_knowledge=update_student_knowledge,
            cognitive_model=cognitive_model,
        ).run_lesson(
            lesson_id=f"{class_id}_simulation_cycle_{cycle_index:02d}",
            student_ids=student_ids,
            lesson_plan=lesson_plan,
            curriculum=curriculum,
            initial_teacher_beliefs=teacher_beliefs,
        )
        teacher_beliefs = session_result["final_teacher_beliefs"]
        cycle_metrics = _cycle_metrics(
            cycle_index=cycle_index,
            lecture_design=lecture_design,
            session_result=session_result,
            teacher_beliefs=teacher_beliefs,
        )
        phase_rows = _phase_rows(cycle_index, session_result)
        timeline_rows.extend(phase_rows)
        cycles_result.append(
            {
                "cycle_index": cycle_index,
                "lecture_design": lecture_design,
                "session_result": session_result,
                "cycle_metrics": cycle_metrics,
                "phase_rows": phase_rows,
            }
        )

    return {
        "experiment": "simulation_timeline",
        "conditions": {
            "class_id": class_id,
            "student_count": len(student_ids),
            "cycles": cycles,
            "total_minutes": total_minutes,
            "teacher_id": teacher_id,
            "use_llm_student": use_llm_student,
            "use_llm_communication": use_llm_communication,
            "model_id": model_id if (use_llm_student or use_llm_communication) else "rule-based/mock",
            "load_in_4bit": load_in_4bit,
            "cognitive_model": cognitive_model.model_name,
            "update_student_knowledge": update_student_knowledge,
            "reset_teacher_beliefs": reset_teacher_beliefs,
            "git_commit": _git_commit(),
        },
        "student_ids": student_ids,
        "cycles": cycles_result,
        "timeline_rows": timeline_rows,
        "cycle_summary_rows": [item["cycle_metrics"] for item in cycles_result],
        "research_metrics": _research_metrics(timeline_rows, cycles_result),
        "issue_candidates": _issue_candidates(timeline_rows, cycles_result),
    }


def export_simulation_timeline_results(
    result: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    stem: str = "simulation_timeline",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    txt_path = output_dir / f"{stem}_for_codex.txt"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    txt_path.write_text(_human_report(result), encoding="utf-8")
    return {"json": str(json_path), "txt": str(txt_path)}


def _cycle_metrics(*, cycle_index: int, lecture_design: dict[str, Any], session_result: dict[str, Any], teacher_beliefs: dict[str, Any]) -> dict[str, Any]:
    summary = session_result["summary"]
    class_profile = session_result["final_class_profile"]
    lesson_goal = session_result["lesson_goal"]
    events = [event for turn in session_result["turns"] for event in turn["events"]]
    graded = [event for event in events if event.get("is_correct") is not None]
    response_times = [event.get("response_time_sec") for event in events if event.get("response_time_sec") is not None]
    confidences = _belief_confidences(teacher_beliefs)
    return {
        "cycle_index": cycle_index,
        "target_skill": lesson_goal.get("target_skill"),
        "goal_text": lesson_goal.get("goal_text"),
        "pace": lecture_design["recommended_lecture"]["whole_class_policy"].get("pace"),
        "accuracy": summary.get("accuracy"),
        "correct_count": summary.get("correct_count"),
        "graded_event_count": summary.get("graded_event_count"),
        "average_estimated_score": class_profile.get("average_estimated_score"),
        "score_std": class_profile.get("score_std"),
        "low_score_count": len(class_profile.get("low_score_students", [])),
        "high_score_count": len(class_profile.get("high_score_students", [])),
        "common_risk_count": len(class_profile.get("common_risks", [])),
        "estimated_misconception_count": sum(len(b.get("estimated_misconceptions", [])) for b in teacher_beliefs.values()),
        "average_belief_confidence": round(mean(confidences), 3) if confidences else 0.0,
        "average_response_time_sec": round(mean(response_times), 3) if response_times else None,
        "event_count": len(events),
        "graded_accuracy_available": bool(graded),
    }


def _phase_rows(cycle_index: int, session_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for turn in session_result.get("turns", []):
        events = turn.get("events", [])
        graded = [event for event in events if event.get("is_correct") is not None]
        correct = sum(1 for event in graded if event.get("is_correct") is True)
        response_times = [event.get("response_time_sec") for event in events if event.get("response_time_sec") is not None]
        observation = turn.get("classroom_observation", {})
        priority_students = observation.get("priority_students", [])
        trait_counts = observation.get("trait_level_counts", {})
        rows.append(
            {
                "cycle_index": cycle_index,
                "phase_index": turn.get("phase_index"),
                "phase": turn.get("phase", {}).get("phase"),
                "minutes": turn.get("phase", {}).get("minutes"),
                "expected_answer": turn.get("expected_answer"),
                "event_count": len(events),
                "graded_event_count": len(graded),
                "accuracy": round(correct / len(graded), 3) if graded else None,
                "priority_student_count": len(priority_students),
                "low_self_efficacy_count": trait_counts.get("self_efficacy", {}).get("low", 0),
                "low_question_tendency_count": trait_counts.get("question_tendency", {}).get("low", 0),
                "low_motivation_count": trait_counts.get("motivation", {}).get("low", 0),
                "high_neuroticism_count": trait_counts.get("neuroticism", {}).get("high", 0),
                "average_response_time_sec": round(mean(response_times), 3) if response_times else None,
                "teacher_message": turn.get("teacher_message"),
            }
        )
    return rows


def _research_metrics(timeline_rows: list[dict[str, Any]], cycles_result: list[dict[str, Any]]) -> dict[str, Any]:
    cycle_rows = [item["cycle_metrics"] for item in cycles_result]
    accuracies = [row["accuracy"] for row in cycle_rows if row["accuracy"] is not None]
    confidence_values = [row["average_belief_confidence"] for row in cycle_rows]
    return {
        "accuracy_first": accuracies[0] if accuracies else None,
        "accuracy_last": accuracies[-1] if accuracies else None,
        "accuracy_delta": round(accuracies[-1] - accuracies[0], 3) if len(accuracies) >= 2 else None,
        "belief_confidence_first": confidence_values[0] if confidence_values else None,
        "belief_confidence_last": confidence_values[-1] if confidence_values else None,
        "belief_confidence_delta": round(confidence_values[-1] - confidence_values[0], 3) if len(confidence_values) >= 2 else None,
        "target_skill_sequence": [row["target_skill"] for row in cycle_rows],
        "pace_sequence": [row["pace"] for row in cycle_rows],
        "phase_count": len(timeline_rows),
        "graded_phase_count": sum(1 for row in timeline_rows if row["accuracy"] is not None),
    }


def _issue_candidates(timeline_rows: list[dict[str, Any]], cycles_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues = []
    for row in timeline_rows:
        if row["accuracy"] is not None and row["accuracy"] < 0.5:
            issues.append({"type": "low_phase_accuracy", "row": row, "note": "このフェーズで正答率が低い。問題難易度、説明、誤概念推定を確認する。"})
        if row["priority_student_count"] > max(2, row["event_count"] // 2):
            issues.append({"type": "many_priority_students", "row": row, "note": "要支援判定がクラスの半数を超えている。伝達AIの閾値または発話生成を確認する。"})
    cycle_rows = [item["cycle_metrics"] for item in cycles_result]
    accuracies = [row["accuracy"] for row in cycle_rows if row.get("accuracy") is not None]
    if len(accuracies) >= 2 and all(value >= 0.95 for value in accuracies):
        issues.append({"type": "accuracy_saturation", "row": cycle_rows[-1], "note": "正答率が高止まりしている。問題難易度や弱点スキル条件を上げないと授業手法の差が見えにくい。"})
    if len(cycle_rows) >= 2 and cycle_rows[-1]["average_belief_confidence"] < cycle_rows[0]["average_belief_confidence"]:
        issues.append({"type": "belief_confidence_decreased", "row": cycle_rows[-1], "note": "時間経過で教師beliefの確信度が下がっている。矛盾観察の扱いを確認する。"})
    return issues[:10]


def _belief_confidences(teacher_beliefs: dict[str, Any]) -> list[float]:
    values = []
    for belief in teacher_beliefs.values():
        linear = belief.get("estimated_knowledge", {}).get("linear_equation", {})
        values.append(float(linear.get("confidence", 0.0)))
        for estimate in belief.get("estimated_traits", {}).values():
            values.append(float(estimate.get("confidence", 0.0)))
        for item in belief.get("estimated_misconceptions", []):
            values.append(float(item.get("confidence", 0.0)))
    return values


def _human_report(result: dict[str, Any]) -> str:
    lines = [
        "# Simulation Timeline For Codex",
        "",
        "このファイルは、教育シミュレーションを時間経過で回した結果です。",
        "",
        "## Conditions",
        json.dumps(result["conditions"], ensure_ascii=False, indent=2),
        "",
        "## Research Metrics",
        json.dumps(result["research_metrics"], ensure_ascii=False, indent=2),
        "",
        "## Cycle Summary",
        "cycle\ttarget_skill\tpace\taccuracy\tavg_estimated_score\tbelief_confidence\tavg_response_time\tmisconception_count",
    ]
    for row in result["cycle_summary_rows"]:
        lines.append("\t".join([
            str(row["cycle_index"]),
            str(row["target_skill"]),
            str(row["pace"]),
            str(row["accuracy"]),
            str(row["average_estimated_score"]),
            str(row["average_belief_confidence"]),
            str(row["average_response_time_sec"]),
            str(row["estimated_misconception_count"]),
        ]))
    lines.extend([
        "",
        "## Timeline Rows",
        "cycle\tphase\taccuracy\tpriority_count\tlow_self\tlow_question\tlow_motivation\thigh_anxiety\tavg_response_time",
    ])
    for row in result["timeline_rows"]:
        lines.append("\t".join([
            str(row["cycle_index"]),
            str(row["phase"]),
            str(row["accuracy"]),
            str(row["priority_student_count"]),
            str(row["low_self_efficacy_count"]),
            str(row["low_question_tendency_count"]),
            str(row["low_motivation_count"]),
            str(row["high_neuroticism_count"]),
            str(row["average_response_time_sec"]),
        ]))
    lines.extend(["", "## Issue Candidates", json.dumps(result["issue_candidates"], ensure_ascii=False, indent=2)])
    return "\n".join(lines).rstrip() + "\n"


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def _reset_generated_dir(path: Path) -> None:
    path = Path(path)
    if path.exists():
        # This directory is generated experiment state, not source data.
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
