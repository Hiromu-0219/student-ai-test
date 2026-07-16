from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from src.state_manager import StateManager


REQUIRED_CLASS_FIELDS = {
    "class_id",
    "student_ids",
    "class_features",
}


class ClassDefinitionError(ValueError):
    """Raised when a class definition file is missing required data."""


class ClassManager:
    def __init__(
        self,
        classes_dir: str | Path = "data/classes",
        students_dir: str | Path = "data/students",
    ) -> None:
        self.classes_dir = Path(classes_dir)
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.state_manager = StateManager(students_dir)

    def class_path(self, class_id: str) -> Path:
        safe_id = class_id.strip()
        if not safe_id:
            raise ClassDefinitionError("class_id must not be empty")
        return self.classes_dir / f"{safe_id}.json"

    def list_classes(self) -> list[str]:
        return sorted(path.stem for path in self.classes_dir.glob("*.json"))

    def load_class(self, class_id: str) -> dict[str, Any]:
        path = self.class_path(class_id)
        if not path.exists():
            raise FileNotFoundError(f"Class definition not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            class_state = json.load(f)

        self.validate_class(class_state)
        return class_state

    def load_students(self, class_id: str) -> list[dict[str, Any]]:
        class_state = self.load_class(class_id)
        return [
            self.state_manager.load_student(student_id)
            for student_id in class_state["student_ids"]
        ]

    def summarize_class(self, class_id: str) -> dict[str, Any]:
        class_state = self.load_class(class_id)
        students = self.load_students(class_id)
        scores = [
            self._linear_equation_score(student_state)
            for student_state in students
        ]

        misconception_students = [
            student_state["student_id"]
            for student_state in students
            if student_state.get("misconceptions")
        ]

        return {
            "class_id": class_state["class_id"],
            "name": class_state.get("name", class_state["class_id"]),
            "student_count": len(students),
            "student_ids": class_state["student_ids"],
            "class_features": class_state["class_features"],
            "tags": class_state.get("tags", []),
            "average_score": round(mean(scores), 1) if scores else 0,
            "score_std": round(pstdev(scores), 1) if len(scores) > 1 else 0.0,
            "low_score_students": [
                student_state["student_id"]
                for student_state, score in zip(students, scores)
                if score < 45
            ],
            "high_score_students": [
                student_state["student_id"]
                for student_state, score in zip(students, scores)
                if score >= 65
            ],
            "trait_counts": {
                "self_efficacy": self._count_trait(students, "self_efficacy"),
                "question_tendency": self._count_trait(students, "question_tendency"),
                "motivation": self._count_trait(students, "motivation"),
                "neuroticism": self._count_big_five_trait(students, "neuroticism"),
            },
            "misconception_count": len(misconception_students),
            "misconception_students": misconception_students,
        }

    @staticmethod
    def validate_class(class_state: dict[str, Any]) -> None:
        missing = REQUIRED_CLASS_FIELDS - set(class_state)
        if missing:
            raise ClassDefinitionError(f"Missing class fields: {sorted(missing)}")

        if not isinstance(class_state["class_id"], str) or not class_state["class_id"].strip():
            raise ClassDefinitionError("class_id must be a non-empty string")

        student_ids = class_state["student_ids"]
        if not isinstance(student_ids, list) or not student_ids:
            raise ClassDefinitionError("student_ids must be a non-empty list")
        if any(not isinstance(student_id, str) or not student_id.strip() for student_id in student_ids):
            raise ClassDefinitionError("student_ids must contain non-empty strings")
        if len(set(student_ids)) != len(student_ids):
            raise ClassDefinitionError("student_ids must not contain duplicates")

        if not isinstance(class_state["class_features"], dict):
            raise ClassDefinitionError("class_features must be an object")

        if "tags" in class_state and not isinstance(class_state["tags"], list):
            raise ClassDefinitionError("tags must be a list when present")

    @staticmethod
    def _linear_equation_score(student_state: dict[str, Any]) -> int:
        linear_state = student_state.get("knowledge_state", {}).get("linear_equation", {})
        score = linear_state.get("score", 0)
        return score if isinstance(score, int) else 0

    @staticmethod
    def _count_trait(students: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts = {"very_low": 0, "low": 0, "medium": 0, "high": 0, "very_high": 0}
        for student_state in students:
            value = student_state.get(field)
            if value in counts:
                counts[value] += 1
        return counts

    @staticmethod
    def _count_big_five_trait(students: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts = {"very_low": 0, "low": 0, "medium": 0, "high": 0, "very_high": 0}
        for student_state in students:
            value = student_state.get("big_five", {}).get(field)
            if value in counts:
                counts[value] += 1
        return counts
