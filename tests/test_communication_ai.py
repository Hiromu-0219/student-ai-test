import pytest

from src.observer import CommunicationAI, LLMCommunicationAI


def test_communication_ai_classifies_short_reserved_student():
    result = CommunicationAI().classify_utterance(
        utterance="x = 4",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "C"
    assert result.trait_estimates["extraversion"] == "low"
    assert result.trait_estimates["motivation"] == "low"
    assert result.trait_estimates["conscientiousness"] == "low"


def test_communication_ai_classifies_long_talkative_student():
    result = CommunicationAI().classify_utterance(
        utterance=(
            "I think x equals 4 because I moved the constant first and then checked "
            "the answer by substituting it back into the equation."
        ),
        student_id="S_TEST",
    )

    assert result.profile_prediction == "D"
    assert result.trait_estimates["extraversion"] == "high"


def test_communication_ai_classifies_many_rows():
    rows = [
        {"student_id": "A", "answer": "x = 4"},
        {
            "student_id": "D",
            "answer": (
                "I think x equals 4 because I moved the constant first and then checked "
                "the answer by substituting it back into the equation."
            ),
        },
    ]

    results = CommunicationAI().classify_many(rows)

    assert len(results) == 2
    assert results[0]["profile_prediction"] == "C"
    assert results[1]["profile_prediction"] == "D"


def test_communication_ai_summarizes_classroom():
    rows = [
        {"student_id": "S001", "answer": "x = 4"},
        {"student_id": "S002", "answer": "x = 5"},
        {
            "student_id": "S003",
            "answer": (
                "I think x equals 4 because I moved the constant first and then checked "
                "the answer by substituting it back into the equation."
            ),
        },
    ]

    summary = CommunicationAI().summarize_classroom(rows)

    assert summary.student_count == 3
    assert len(summary.individual_results) == 3
    assert sum(summary.profile_counts.values()) == 3
    assert "self_efficacy" in summary.trait_level_counts
    assert summary.priority_students == []
    assert summary.recommended_teacher_actions
    assert summary.to_dict()["student_count"] == 3


def test_communication_ai_prioritizes_observable_incorrect_answers():
    rows = [
        {
            "student_id": "S001",
            "answer": "x = 8",
            "observable_event": {
                "is_correct": False,
                "showed_work": False,
                "no_response": False,
            },
        },
        {
            "student_id": "S002",
            "answer": "まず両辺を2で割ります。x = 4",
            "observable_event": {
                "is_correct": True,
                "showed_work": True,
                "no_response": False,
            },
        },
        {
            "student_id": "S003",
            "answer": "x = 4",
            "observable_event": {
                "is_correct": True,
                "showed_work": False,
                "no_response": False,
            },
        },
    ]

    summary = CommunicationAI().summarize_classroom(rows)

    assert [student["student_id"] for student in summary.priority_students] == ["S001"]
    assert "incorrect_answer" in summary.priority_students[0]["priority_reasons"]

def test_communication_ai_rejects_classroom_size_outside_expected_range():
    rows = [
        {"student_id": "S001", "answer": "x = 4"},
        {"student_id": "S002", "answer": "x = 4"},
    ]

    with pytest.raises(ValueError, match="3-20 students"):
        CommunicationAI().summarize_classroom(rows)


class FakeClassifierLLM:
    model_id = "fake-classifier"

    def __init__(self, output: str) -> None:
        self.output = output

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return self.output


def test_llm_communication_ai_uses_json_classification():
    llm_output = """
{
  "profile_prediction": "D",
  "trait_estimates": {
    "self_efficacy": "high",
    "question_tendency": "high",
    "motivation": "high",
    "extraversion": "high",
    "conscientiousness": "medium",
    "neuroticism": "low"
  },
  "evidence": ["confident explanation"],
  "confidence": 0.91,
  "teacher_summary": "Confident and talkative student.",
  "recommended_teacher_attention": ["Ask a deeper follow-up question."]
}
""".strip()

    result = LLMCommunicationAI(FakeClassifierLLM(llm_output)).classify_utterance(
        utterance="I can explain this clearly.",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "D"
    assert result.trait_estimates["self_efficacy"] == "high"
    assert result.confidence == 0.91
    assert result.recommended_teacher_attention == ["Ask a deeper follow-up question."]


def test_llm_communication_ai_falls_back_on_invalid_json():
    result = LLMCommunicationAI(FakeClassifierLLM("not json")).classify_utterance(
        utterance="x = 4",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "C"


def test_llm_communication_ai_calibrates_empty_high_claim_to_reserved():
    llm_output = """
{
  "profile_prediction": "B",
  "trait_estimates": {
    "self_efficacy": "high",
    "question_tendency": "high",
    "motivation": "high",
    "extraversion": "high",
    "conscientiousness": "high",
    "neuroticism": "low"
  },
  "evidence": ["claims confidence"],
  "confidence": 0.95,
  "teacher_summary": "High confidence student.",
  "recommended_teacher_attention": ["extension"]
}
""".strip()

    result = LLMCommunicationAI(FakeClassifierLLM(llm_output)).classify_utterance(
        utterance="",
        student_id="S_EMPTY",
    )

    assert result.profile_prediction == "C"
    assert result.trait_estimates["self_efficacy"] == "low"
    assert result.trait_estimates["question_tendency"] == "low"
    assert result.trait_estimates["motivation"] == "low"
    assert result.confidence <= 0.65


def test_llm_communication_ai_calibrates_short_answer_question_tendency():
    llm_output = """
{
  "profile_prediction": "D",
  "trait_estimates": {
    "self_efficacy": "high",
    "question_tendency": "high",
    "motivation": "high",
    "extraversion": "high",
    "conscientiousness": "high",
    "neuroticism": "low"
  },
  "evidence": ["short answer"],
  "confidence": 0.92,
  "teacher_summary": "Confident student.",
  "recommended_teacher_attention": ["extension"]
}
""".strip()

    result = LLMCommunicationAI(FakeClassifierLLM(llm_output)).classify_utterance(
        utterance="3を除きましょう。",
        student_id="S_SHORT",
    )

    assert result.profile_prediction == "C"
    assert result.trait_estimates["question_tendency"] == "low"
    assert result.trait_estimates["motivation"] == "low"
    assert result.trait_estimates["extraversion"] == "low"
    assert result.confidence <= 0.7
