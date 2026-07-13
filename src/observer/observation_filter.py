from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ObservableEvent:
    """Information that can be observed during a lesson.

    This intentionally excludes true internal student parameters such as
    knowledge_state, big_five, motivation, and misconceptions.
    """

    lesson_id: str
    teacher_id: str
    student_id: str
    teacher_prompt: str
    utterance: str
    answer: str | None
    is_correct: bool | None
    response_time_sec: float | None
    asked_question: bool
    showed_work: bool
    revision_count: int
    no_response: bool
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "teacher_id": self.teacher_id,
            "student_id": self.student_id,
            "teacher_prompt": self.teacher_prompt,
            "utterance": self.utterance,
            "answer": self.answer,
            "is_correct": self.is_correct,
            "response_time_sec": self.response_time_sec,
            "asked_question": self.asked_question,
            "showed_work": self.showed_work,
            "revision_count": self.revision_count,
            "no_response": self.no_response,
            "timestamp": self.timestamp,
        }


def build_observable_event(
    *,
    lesson_id: str,
    teacher_id: str,
    student_id: str,
    teacher_prompt: str,
    utterance: str,
    answer: str | None = None,
    is_correct: bool | None = None,
    response_time_sec: float | None = None,
    revision_count: int = 0,
    timestamp: str | None = None,
) -> ObservableEvent:
    text = utterance or ""
    return ObservableEvent(
        lesson_id=lesson_id,
        teacher_id=teacher_id,
        student_id=student_id,
        teacher_prompt=teacher_prompt,
        utterance=text,
        answer=answer,
        is_correct=is_correct,
        response_time_sec=response_time_sec,
        asked_question=_asked_question(text),
        showed_work=_showed_work(text),
        revision_count=max(0, revision_count),
        no_response=not text.strip(),
        timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
    )


def event_to_communication_row(event: ObservableEvent | dict[str, Any]) -> dict[str, Any]:
    data = event.to_dict() if hasattr(event, "to_dict") else dict(event)
    return {
        "student_id": data["student_id"],
        "answer": data.get("utterance", ""),
        "observable_event": data,
    }


def events_to_communication_rows(
    events: list[ObservableEvent | dict[str, Any]],
) -> list[dict[str, Any]]:
    return [event_to_communication_row(event) for event in events]


def _asked_question(text: str) -> bool:
    return any(token in text for token in ["?", "？", "ですか", "ますか", "合っていますか"])


def _showed_work(text: str) -> bool:
    return any(token in text for token in ["まず", "それから", "両辺", "移項", "係数", "="])
