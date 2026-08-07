from __future__ import annotations

import re
import unicodedata
from fractions import Fraction
from typing import Any


class LinearEquationGrader:
    def grade(self, expected_answer: str, student_answer: str) -> dict[str, Any]:
        expected = extract_x_value(expected_answer)
        actual = extract_x_value(student_answer)
        is_correct = expected is not None and actual is not None and expected == actual
        return {
            "is_correct": is_correct,
            "score": 1 if is_correct else 0,
            "expected_value": str(expected) if expected is not None else None,
            "student_value": str(actual) if actual is not None else None,
        }


def extract_x_value(text: str) -> Fraction | None:
    normalized = _normalize_text(text)
    compact = re.sub(r"\s+", "", normalized)

    answer_labeled = _last_number_from_patterns(
        compact,
        [
            r"(?:答え|解答|答|answer)[:：は=]*x?=?([+-]?\d+(?:/\d+)?)",
            r"(?:答え|解答|答|answer)[:：は=]*(?:xの値は|xは|xが)([+-]?\d+(?:/\d+)?)",
        ],
    )
    if answer_labeled is not None:
        return answer_labeled

    explicit_x = _last_number_from_patterns(
        compact,
        [
            r"(?<![0-9A-Za-z])x=([+-]?\d+(?:/\d+)?)",
            r"(?<![0-9A-Za-z])x(?:は|が|の値は|になる)([+-]?\d+(?:/\d+)?)",
        ],
    )
    if explicit_x is not None:
        return explicit_x

    english_x = _last_number_from_patterns(
        normalized,
        [
            r"\bx\s*(?:=|equals|is)\s*([+-]?\d+(?:/\d+)?)",
            r"\bthe\s+answer\s+is\s+([+-]?\d+(?:/\d+)?)",
        ],
    )
    if english_x is not None:
        return english_x

    return None


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text)).lower()


def _last_number_from_patterns(text: str, patterns: list[str]) -> Fraction | None:
    matches: list[Fraction] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = _parse_number(match.group(1))
            if value is not None:
                matches.append(value)
    return matches[-1] if matches else None


def _parse_number(value: str) -> Fraction | None:
    try:
        return Fraction(value)
    except ValueError:
        return None
