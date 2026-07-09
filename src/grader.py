from __future__ import annotations

import re
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
    normalized = text.replace(" ", "").replace("　", "")
    patterns = [
        r"x=([+-]?\d+(?:/\d+)?)",
        r"答え[:：]?x=([+-]?\d+(?:/\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return _parse_number(match.group(1))
    return None


def _parse_number(value: str) -> Fraction | None:
    try:
        return Fraction(value)
    except ValueError:
        return None
