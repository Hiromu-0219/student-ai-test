from __future__ import annotations

from typing import Any, Protocol

from src.prompts import SYSTEM_PROMPT, build_student_prompt


class SpeechGenerator(Protocol):
    model_id: str

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass


class StudentAgent:
    def __init__(self, speech_generator: SpeechGenerator) -> None:
        self.speech_generator = speech_generator

    @property
    def model_id(self) -> str:
        return self.speech_generator.model_id

    def answer(self, student_state: dict[str, Any], problem: str) -> str:
        prompt = build_student_prompt(student_state, problem)
        return self.speech_generator.generate(SYSTEM_PROMPT, prompt)
