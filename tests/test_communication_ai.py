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
    assert summary.priority_students
    assert summary.recommended_teacher_actions
    assert summary.to_dict()["student_count"] == 3


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
