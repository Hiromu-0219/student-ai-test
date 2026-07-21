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
    if assessment:
        text = _remove_teacher_lines(text)
        text = _remove_empty_lines(text)
        return _keep_assessment_answer(text)
    text = _keep_only_student_speaker_turn(text)
    text = _remove_empty_lines(text)
    return _limit_sentences(text, max_sentences=4)


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```(?:text|markdown|json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def _speaker_pattern(names: list[str]) -> re.Pattern[str]:
    joined = "|".join(re.escape(name) for name in names)
    return re.compile(rf"^\s*(?:{joined})\s*[:：]\s*")


TEACHER_PREFIX = _speaker_pattern(["教師", "先生", "Teacher"])
STUDENT_PREFIX = _speaker_pattern(["生徒", "学生", "Student"])


def _keep_only_student_speaker_turn(text: str) -> str:
    lines = []
    saw_student_label = False
    captured_after_student_label = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if TEACHER_PREFIX.match(line):
            if captured_after_student_label:
                break
            continue

        student_match = STUDENT_PREFIX.match(line)
        if student_match:
            if captured_after_student_label:
                break
            saw_student_label = True
            captured_after_student_label = True
            stripped = STUDENT_PREFIX.sub("", line).strip()
            if stripped:
                lines.append(stripped)
            continue

        if saw_student_label or not _looks_like_dialogue_label(line):
            lines.append(_remove_inline_speaker_labels(line))

    return "\n".join(lines).strip()


def _looks_like_dialogue_label(line: str) -> bool:
    return bool(re.match(r"^\s*[^:：]{1,12}\s*[:：]", line))


def _remove_inline_speaker_labels(line: str) -> str:
    line = TEACHER_PREFIX.sub("", line)
    line = STUDENT_PREFIX.sub("", line)
    return line.strip()


def _remove_empty_lines(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def _remove_teacher_lines(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not TEACHER_PREFIX.match(line.strip())
    ).strip()


def _keep_assessment_answer(text: str) -> str:
    answer_matches = re.findall(r"答え\s*[:：]\s*x\s*=\s*[^\s。！？?]+", text)
    if answer_matches:
        return answer_matches[-1].replace("答え：", "答え:").strip()
    return _limit_sentences(text, max_sentences=1)


def _limit_sentences(text: str, *, max_sentences: int) -> str:
    if not text:
        return text
    answer_match = re.search(r"(答え\s*[:：]\s*x\s*=\s*[^\s。！？?]+)", text)
    answer_part = answer_match.group(1).replace("答え：", "答え:") if answer_match else None
    before_answer = text[: answer_match.start()].strip() if answer_match else text
    pieces = re.findall(r"[^。！？?]+[。！？?]?", before_answer)
    limited = "".join(piece.strip() for piece in pieces[:max_sentences]).strip()
    if answer_part and answer_part not in limited:
        limited = f"{limited} {answer_part}".strip()
    return limited or (answer_part or text)
