from src.personality_model import build_personality_profile
from src.prompts import build_student_prompt
from src.student_ai import RuleBasedMockLLM


def base_state():
    return {
        "student_id": "P001",
        "name": "Personality Test",
        "understanding": {"linear_equation": "basic"},
        "knowledge_state": {"linear_equation": {"score": 50}},
        "error_tendency": [],
        "misconceptions": [],
        "learning_speed": "medium",
        "personality": {},
        "big_five": {
            "openness": "medium",
            "conscientiousness": "medium",
            "extraversion": "medium",
            "agreeableness": "medium",
            "neuroticism": "medium",
        },
        "self_efficacy": "medium",
        "question_tendency": "medium",
        "motivation": "medium",
        "learning_history": [],
    }


def test_personality_profile_turns_traits_into_speech_instructions():
    state = base_state()
    state["self_efficacy"] = "low"
    state["question_tendency"] = "high"
    state["motivation"] = "high"
    state["big_five"]["neuroticism"] = "very_high"
    state["big_five"]["conscientiousness"] = "high"

    profile = build_personality_profile(state)

    assert profile["confidence_expression"] == "low"
    assert profile["question_behavior"] == "asks_specific_questions"
    assert profile["emotional_tone"] == "anxious"
    assert "自信なさげに、断定を避けて答える。" in profile["prompt_instructions"]
    assert "わからない点があれば具体的に質問する。" in profile["prompt_instructions"]


def test_student_prompt_contains_personality_instructions():
    state = base_state()
    state["self_efficacy"] = "very_low"
    state["question_tendency"] = "high"

    prompt = build_student_prompt(state, "2x+3=11 を解いてください")

    assert "発話スタイル:" in prompt
    assert "自信なさげに、断定を避けて答える。" in prompt
    assert "わからない点があれば具体的に質問する。" in prompt


def test_mock_llm_reflects_personality_style():
    state = base_state()
    state["self_efficacy"] = "very_low"
    state["question_tendency"] = "high"
    state["big_five"]["neuroticism"] = "high"
    prompt = build_student_prompt(state, "2x+3=11 を解いてください")

    answer = RuleBasedMockLLM().generate("system", prompt)

    assert "自信はないけど" in answer
    assert "不安" in answer
    assert "移項の符号" in answer
    assert "答え: x = 4" in answer
