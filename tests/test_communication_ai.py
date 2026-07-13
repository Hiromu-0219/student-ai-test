from src.observer import CommunicationAI, LLMCommunicationAI


def test_communication_ai_classifies_anxious_questioning_student():
    result = CommunicationAI().classify_utterance(
        utterance="自信はないけど、x = 4 だと思います。符号が合っているか少し不安です。移項の符号はこの考え方で合っていますか？ 答え: x = 4",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "A"
    assert result.trait_estimates["self_efficacy"] == "low"
    assert result.trait_estimates["question_tendency"] == "high"
    assert result.trait_estimates["neuroticism"] == "high"
    assert "不安" in result.teacher_summary
    assert result.recommended_teacher_attention


def test_communication_ai_classifies_short_reserved_student():
    result = CommunicationAI().classify_utterance(
        utterance="x = 4。 答え: x = 4",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "C"
    assert result.trait_estimates["extraversion"] == "low"
    assert result.trait_estimates["motivation"] == "low"
    assert result.trait_estimates["conscientiousness"] == "low"


def test_communication_ai_classifies_many_rows():
    rows = [
        {"student_id": "A", "answer": "自信はないけど、x = 4。不安です。合っていますか？"},
        {"student_id": "C", "answer": "x = 4。"},
    ]

    results = CommunicationAI().classify_many(rows)

    assert len(results) == 2
    assert results[0]["profile_prediction"] == "A"
    assert results[1]["profile_prediction"] == "C"


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
  "evidence": ["自信を示す表現がある"],
  "confidence": 0.91,
  "teacher_summary": "自信が高く発話量も多い生徒です。",
  "recommended_teacher_attention": ["発展的な問いを出す"]
}
""".strip()

    result = LLMCommunicationAI(FakeClassifierLLM(llm_output)).classify_utterance(
        utterance="これは分かります。x = 4 です。もっと別の解き方も試したいです。",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "D"
    assert result.trait_estimates["self_efficacy"] == "high"
    assert result.confidence == 0.91
    assert result.recommended_teacher_attention == ["発展的な問いを出す"]


def test_llm_communication_ai_falls_back_on_invalid_json():
    result = LLMCommunicationAI(FakeClassifierLLM("not json")).classify_utterance(
        utterance="x = 4。 答え: x = 4",
        student_id="S_TEST",
    )

    assert result.profile_prediction == "C"
