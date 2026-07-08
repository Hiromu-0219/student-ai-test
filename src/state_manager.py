from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


REQUIRED_STUDENT_FIELDS = {
    "student_id",
    "name",
    "understanding",
    "knowledge_state",
    "error_tendency",
    "misconceptions",
    "learning_speed",
    "personality",
    "big_five",
    "self_efficacy",
    "question_tendency",
    "motivation",
    "learning_history",
}


class StudentStateError(ValueError):
    """Raised when a student state file is missing required data."""


class StateManager:
    def __init__(self, students_dir: str | Path = "data/students") -> None:
        self.students_dir = Path(students_dir)
        self.students_dir.mkdir(parents=True, exist_ok=True)

    def student_path(self, student_id: str) -> Path:
        safe_id = student_id.strip()
        if not safe_id:
            raise StudentStateError("student_id must not be empty")
        return self.students_dir / f"{safe_id}.json"

    def load_student(self, student_id: str) -> dict[str, Any]:
        path = self.student_path(student_id)
        if not path.exists():
            raise FileNotFoundError(f"Student state not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            state = json.load(f)

        self.validate_student(state)
        return state

    def save_student(self, state: dict[str, Any]) -> Path:
        self.validate_student(state)
        path = self.student_path(str(state["student_id"]))
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        return path

    def update_learning_history(
        self,
        student_id: str,
        entry: dict[str, Any],
        save: bool = True,
    ) -> dict[str, Any]:
        state = self.load_student(student_id)
        updated = deepcopy(state)
        updated["learning_history"].append(entry)
        if save:
            self.save_student(updated)
        return updated

    @staticmethod
    def validate_student(state: dict[str, Any]) -> None:
        missing = REQUIRED_STUDENT_FIELDS - set(state)
        if missing:
            raise StudentStateError(f"Missing student fields: {sorted(missing)}")

        if not isinstance(state["understanding"], dict):
            raise StudentStateError("understanding must be an object")
        if not isinstance(state["knowledge_state"], dict):
            raise StudentStateError("knowledge_state must be an object")
        if not isinstance(state["error_tendency"], list):
            raise StudentStateError("error_tendency must be a list")
        if not isinstance(state["misconceptions"], list):
            raise StudentStateError("misconceptions must be a list")
        if not isinstance(state["learning_speed"], str):
            raise StudentStateError("learning_speed must be a string")
        if not isinstance(state["personality"], dict):
            raise StudentStateError("personality must be an object")
        if not isinstance(state["big_five"], dict):
            raise StudentStateError("big_five must be an object")
        if not isinstance(state["self_efficacy"], str):
            raise StudentStateError("self_efficacy must be a string")
        if not isinstance(state["question_tendency"], str):
            raise StudentStateError("question_tendency must be a string")
        if not isinstance(state["motivation"], str):
            raise StudentStateError("motivation must be a string")
        if not isinstance(state["learning_history"], list):
            raise StudentStateError("learning_history must be a list")
