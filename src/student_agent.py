from __future__ import annotations

import re
from typing import Any, Protocol

from src.prompts import (
    ASSESSMENT_SYSTEM_PROMPT,
    CONTROLLED_LESSON_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_student_prompt,
)


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
        directive_mode = (assessment_directive or {}).get("mode")
        if directive_mode == "lesson_probe":
            system_prompt = CONTROLLED_LESSON_SYSTEM_PROMPT
            is_assessment = False
        elif assessment_directive:
            system_prompt = ASSESSMENT_SYSTEM_PROMPT
            is_assessment = True
        else:
            system_prompt = SYSTEM_PROMPT
            is_assessment = False
        raw_answer = self.speech_generator.generate(system_prompt, prompt)
        normalized_answer = normalize_student_turn(
            raw_answer,
            assessment=is_assessment,
            teacher_message=problem,
        )
        if directive_mode == "lesson_probe":
            return _force_controlled_answer_label(
                normalized_answer,
                (assessment_directive or {}).get("target_answer"),
            )
        return normalized_answer


def normalize_student_turn(
    raw_answer: str,
    *,
    assessment: bool = False,
    teacher_message: str | None = None,
) -> str:
    """Keep only one student turn and remove accidental teacher dialogue."""

    text = str(raw_answer).strip()
    text = _strip_code_fence(text)
    if assessment:
        text = _remove_teacher_lines(text)
        text = _remove_empty_lines(text)
        return _keep_assessment_answer(text)
    text = _keep_only_student_speaker_turn(text)
    text = _remove_empty_lines(text)
    text = _ensure_non_empty_answer(text)
    text = _ensure_answer_for_linear_problem(text, teacher_message)
    return _limit_sentences(text, max_sentences=4)


def _force_controlled_answer_label(text: str, target_answer: str | None) -> str:
    if not target_answer:
        return text
    answer_label = _normalize_answer_label(f"答え: {target_answer}")
    text = _normalize_answer_label(text).strip()
    text = re.sub(r"答え\s*[:：]\s*(?:x\s*=\s*)?[^\s。！？?]+", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return f"{text} {answer_label}".strip() if text else answer_label


def _ensure_non_empty_answer(text: str) -> str:
    return text.strip() or "答え: わかりません"


def _ensure_answer_for_linear_problem(text: str, teacher_message: str | None) -> str:
    if not teacher_message or re.search(r"答え\s*[:：]", text):
        return text
    inferred = _infer_linear_equation_answer(teacher_message)
    if inferred is None:
        return text
    if re.search(rf"x\s*=\s*{re.escape(inferred)}(?![\d/])", text):
        return f"{text} 答え: x = {inferred}"
    return f"{text} 答え: x = {inferred}"


def _infer_linear_equation_answer(text: str) -> str | None:
    compact = text.replace(" ", "")
    match = re.search(r"([+-]?\d*)x=([+-]?\d+)", compact)
    if match:
        coef_text, rhs_text = match.groups()
        if coef_text in {"", "+"}:
            coef = 1
        elif coef_text == "-":
            coef = -1
        else:
            coef = int(coef_text)
        rhs = int(rhs_text)
        if coef == 0:
            return None
        if rhs % coef == 0:
            return str(rhs // coef)
        return f"{rhs}/{coef}"

    match = re.search(r"([+-]?\d*)x([+-]\d+)=([+-]?\d+)", compact)
    if match:
        coef_text, const_text, rhs_text = match.groups()
        if coef_text in {"", "+"}:
            coef = 1
        elif coef_text == "-":
            coef = -1
        else:
            coef = int(coef_text)
        const = int(const_text)
        rhs = int(rhs_text)
        numerator = rhs - const
        if coef == 0:
            return None
        if numerator % coef == 0:
            return str(numerator // coef)
        return f"{numerator}/{coef}"
    return None


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
    if "答え:" in line or "答え：" in line:
        return False
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
    text = _normalize_answer_label(text)
    answer_matches = re.findall(r"答え\s*[:：]\s*x\s*=\s*[^\s。！？?]+", text)
    if answer_matches:
        return answer_matches[-1].replace("答え：", "答え:").strip()
    return _limit_sentences(text, max_sentences=1)


def _limit_sentences(text: str, *, max_sentences: int) -> str:
    if not text:
        return text
    text = _normalize_answer_label(text)
    answer_match = re.search(r"(答え\s*[:：]\s*x\s*=\s*[^\s。！？?]+)", text)
    answer_part = answer_match.group(1).replace("答え：", "答え:") if answer_match else None
    before_answer = text[: answer_match.start()].strip() if answer_match else text
    pieces = re.findall(r"[^。！？?]+[。！？?]?", before_answer)
    limited = "".join(piece.strip() for piece in pieces[:max_sentences]).strip()
    if answer_part and answer_part not in limited:
        limited = f"{limited} {answer_part}".strip()
    return limited or (answer_part or text)


def _normalize_answer_label(text: str) -> str:
    return re.sub(
        r"答え\s*[:：]\s*(?!x\s*=)([+-]?\d+(?:/\d+)?)",
        r"答え: x = \1",
        text,
    )
