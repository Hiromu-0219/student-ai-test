from src.observer import build_observable_event, events_to_communication_rows


def test_build_observable_event_excludes_internal_state():
    event = build_observable_event(
        lesson_id="L001",
        teacher_id="T001",
        student_id="S001",
        teacher_prompt="x + 3 = 8",
        utterance="符号が変わるか不安です。x = 11ですか？",
        answer="x = 11",
        is_correct=False,
        response_time_sec=18.4,
        revision_count=1,
        timestamp="2026-07-13T00:00:00+00:00",
    )
    data = event.to_dict()

    assert data["asked_question"] is True
    assert data["showed_work"] is True
    assert data["is_correct"] is False
    assert "knowledge_state" not in data
    assert "big_five" not in data
    assert "motivation" not in data


def test_events_to_communication_rows_uses_only_observable_utterance():
    event = build_observable_event(
        lesson_id="L001",
        teacher_id="T001",
        student_id="S001",
        teacher_prompt="x + 3 = 8",
        utterance="x = 5",
    )

    rows = events_to_communication_rows([event])

    assert rows == [
        {
            "student_id": "S001",
            "answer": "x = 5",
            "observable_event": event.to_dict(),
        }
    ]
