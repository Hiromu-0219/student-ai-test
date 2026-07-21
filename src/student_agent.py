from __future__ import annotations

import re
from typing import Any, Protocol

from src.prompts import ASSESSMENT_SYSTEM_PROMPT, SYSTEM_PROMPT, build_student_prompt


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

    def answer(
        self,
        student_state: dict[str, Any],
        problem: str,
        assessment_directive: dict[str, Any] | None = None,
    ) -> str:
        prompt = build_student_prompt(student_state, problem, assessment_directive)
        system_prompt = ASSESSMENT_SYSTEM_PROMPT if assessment_directive else SYSTEM_PROMPT
        raw_answer = self.speech_generator.generate(system_prompt, prompt)
        return normalize_student_turn(raw_answer, assessment=assessment_directive is not None)


def normalize_student_turn(raw_answer: str, *, assessment: bool = False) -> str:
    """Keep only one student turn and remove accidental teacher dialogue."""

    text = str(raw_answer).strip()
    text = _strip_code_fence(text)
    text = _remove_speaker_prefix(text)
    text = _cut_before_forbidden_speaker(text)
    text = _remove_empty_lines(text)
    if assessment:
        return _keep_assessment_answer(text)
    return _limit_sentences(text, max_sentences=4)


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```(?:text|markdown|json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def _remove_speaker_prefix(text: str) -> str:
    return re.sub(r"^\s*(生徒|学生|Student)\s*[:：]\s*", "", text).strip()


def _cut_before_forbidden_speaker(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*(教師|先生|Teacher)\s*[:：]", line):
            break
        if lines and re.match(r"^\s*(生徒|学生|Student)\s*[:：]", line):
            break
        lines.append(re.sub(r"^\s*(生徒|学生|Student)\s*[:：]\s*", "", line))
    return "\n".join(lines).strip()


def _remove_empty_lines(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def _keep_assessment_answer(text: str) -> str:
    answer_lines = [line for line in text.splitlines() if "答え:" in line or "答え：" in line]
    if answer_lines:
        return answer_lines[-1].replace("答え：", "答え:").strip()
    return _limit_sentences(text, max_sentences=1)


def _limit_sentences(text: str, *, max_sentences: int) -> str:
    if not text:
        return text
    answer_match = re.search(r"(答え\s*[:：]\s*x\s*=\s*[^\s。．.]+)", text)
    answer_part = answer_match.group(1).replace("答え：", "答え:") if answer_match else None
    before_answer = text[: answer_match.start()].strip() if answer_match else text
    pieces = re.findall(r"[^。！？!?]+[。！？!?]?", before_answer)
    limited = "".join(piece.strip() for piece in pieces[:max_sentences]).strip()
    if answer_part and answer_part not in limited:
        limited = f"{limited} {answer_part}".strip()
    return limited or (answer_part or text)
