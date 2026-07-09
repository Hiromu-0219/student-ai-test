from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TestBank:
    __test__ = False

    def __init__(self, tests_dir: str | Path = "data/tests") -> None:
        self.tests_dir = Path(tests_dir)

    def load_test(self, test_id: str) -> dict[str, Any]:
        path = self.tests_dir / f"{test_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Test not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            test_data = json.load(f)
        self.validate_test(test_data)
        return test_data

    @staticmethod
    def validate_test(test_data: dict[str, Any]) -> None:
        required = {"test_id", "title", "domain", "questions"}
        missing = required - set(test_data)
        if missing:
            raise ValueError(f"Missing test fields: {sorted(missing)}")
        if not isinstance(test_data["questions"], list) or not test_data["questions"]:
            raise ValueError("questions must be a non-empty list")
        for question in test_data["questions"]:
            missing_question = {"question_id", "problem", "answer", "skill", "difficulty"} - set(
                question
            )
            if missing_question:
                raise ValueError(f"Missing question fields: {sorted(missing_question)}")
