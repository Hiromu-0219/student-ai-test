from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRAIT_KEYS = [
    "self_efficacy",
    "question_tendency",
    "motivation",
    "conscientiousness",
    "neuroticism",
]


class TeacherBeliefManager:
    """Store a teacher's estimated view of each student.

    This is separate from the true student state. It should be updated only
    from observable lesson events and communication AI outputs.
    """

    def __init__(self, base_dir: str | Path = "data/teacher_beliefs") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def belief_path(self, teacher_id: str, student_id: str) -> Path:
        teacher_dir = self.base_dir / teacher_id
        teacher_dir.mkdir(parents=True, exist_ok=True)
        return teacher_dir / f"{student_id}.json"

    def load_or_create(self, teacher_id: str, student_id: str) -> dict[str, Any]:
        path = self.belief_path(teacher_id, student_id)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        belief = default_teacher_belief(teacher_id, student_id)
        self.save(belief)
        return belief

    def save(self, belief: dict[str, Any]) -> Path:
        path = self.belief_path(belief["teacher_id"], belief["student_id"])
        with path.open("w", encoding="utf-8") as f:
            json.dump(belief, f, ensure_ascii=False, indent=2)
            f.write("\n")
        return path

    def update_from_observation(
        self,
        *,
        teacher_id: str,
        student_id: str,
        observable_event: dict[str, Any],
        communication_result: dict[str, Any],
        save: bool = True,
    ) -> dict[str, Any]:
        belief = deepcopy(self.load_or_create(teacher_id, student_id))
        now = datetime.now(timezone.utc).isoformat()

        _update_estimated_knowledge(belief, observable_event)
        _update_traits(belief, communication_result)
        _update_misconceptions(belief, observable_event, communication_result)
        belief["evidence_history"].append(
            {
                "lesson_id": observable_event.get("lesson_id"),
                "student_id": student_id,
                "utterance": observable_event.get("utterance"),
                "answer": observable_event.get("answer"),
                "is_correct": observable_event.get("is_correct"),
                "communication_profile": communication_result.get("profile_prediction"),
                "communication_evidence": communication_result.get("evidence", []),
                "timestamp": observable_event.get("timestamp") or now,
            }
        )
        belief["evidence_history"] = belief["evidence_history"][-20:]
        belief["last_updated"] = now
        if save:
            self.save(belief)
        return belief

    def update_many(
        self,
        *,
        teacher_id: str,
        observations: list[dict[str, Any]],
        communication_results: list[dict[str, Any]],
        save: bool = True,
    ) -> dict[str, dict[str, Any]]:
        events_by_student = {event["student_id"]: event for event in observations}
        updated = {}
        for result in communication_results:
            student_id = result["student_id"]
            event = events_by_student.get(student_id)
            if not event:
                continue
            updated[student_id] = self.update_from_observation(
                teacher_id=teacher_id,
                student_id=student_id,
                observable_event=event,
                communication_result=result,
                save=save,
            )
        return updated


def default_teacher_belief(teacher_id: str, student_id: str) -> dict[str, Any]:
    return {
        "teacher_id": teacher_id,
        "student_id": student_id,
        "estimated_knowledge": {
            "linear_equation": {
                "score": 50,
                "confidence": 0.0,
            }
        },
        "estimated_traits": {
            key: {"level": "medium", "confidence": 0.0}
            for key in TRAIT_KEYS
        },
        "estimated_misconceptions": [],
        "evidence_history": [],
        "last_updated": None,
    }


def _update_estimated_knowledge(
    belief: dict[str, Any],
    observable_event: dict[str, Any],
) -> None:
    linear = belief["estimated_knowledge"]["linear_equation"]
    score = int(linear.get("score", 50))
    confidence = float(linear.get("confidence", 0.0))
    is_correct = observable_event.get("is_correct")
    if is_correct is True:
        score += 6
        confidence += 0.08
    elif is_correct is False:
        score -= 6
        confidence += 0.08
    if observable_event.get("no_response"):
        score -= 3
        confidence += 0.03
    if observable_event.get("showed_work"):
        confidence += 0.03
    linear["score"] = max(0, min(100, score))
    linear["confidence"] = round(max(0.0, min(1.0, confidence)), 2)


def _update_traits(
    belief: dict[str, Any],
    communication_result: dict[str, Any],
) -> None:
    trait_estimates = communication_result.get("trait_estimates", {})
    confidence_delta = max(0.03, float(communication_result.get("confidence", 0.5)) * 0.08)
    for key in TRAIT_KEYS:
        observed_level = trait_estimates.get(key)
        if observed_level not in {"low", "medium", "high"}:
            continue
        current = belief["estimated_traits"][key]
        current_level = current.get("level", "medium")
        current_confidence = float(current.get("confidence", 0.0))
        if current_level == observed_level:
            current_confidence += confidence_delta
        elif current_confidence < 0.35:
            current_level = observed_level
            current_confidence += confidence_delta * 0.7
        else:
            current_confidence -= confidence_delta * 0.5
            if current_confidence < 0.25:
                current_level = observed_level
                current_confidence = 0.25
        current["level"] = current_level
        current["confidence"] = round(max(0.0, min(1.0, current_confidence)), 2)


def _update_misconceptions(
    belief: dict[str, Any],
    observable_event: dict[str, Any],
    communication_result: dict[str, Any],
) -> None:
    if observable_event.get("is_correct") is not False:
        return

    text = " ".join(
        str(part)
        for part in [
            observable_event.get("utterance", ""),
            observable_event.get("answer", ""),
            " ".join(communication_result.get("evidence", [])),
        ]
    )
    candidate = None
    if any(token in text for token in ["符号", "移項", "反対側"]):
        candidate = "移項時の符号変化に誤概念がある可能性"
    elif any(token in text for token in ["3x", "係数", "割る", "引く"]):
        candidate = "係数で割る操作に誤概念がある可能性"
    if not candidate:
        return

    misconceptions = belief["estimated_misconceptions"]
    for item in misconceptions:
        if item["name"] == candidate:
            item["confidence"] = round(min(1.0, item.get("confidence", 0.0) + 0.15), 2)
            item["evidence_count"] = int(item.get("evidence_count", 0)) + 1
            return
    misconceptions.append(
        {
            "name": candidate,
            "confidence": 0.35,
            "evidence_count": 1,
        }
    )
