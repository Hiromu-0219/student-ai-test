from __future__ import annotations

import json

import pytest

from src.class_manager import ClassDefinitionError, ClassManager
from src.state_manager import StateManager


def make_student(student_id: str, score: int, self_efficacy: str = "medium") -> dict:
    return {
        "student_id": student_id,
        "name": student_id,
        "understanding": {"linear_equation": f"{score}/100"},
        "knowledge_state": {
            "linear_equation": {
                "level": "medium",
                "score": score,
                "can_solve_ax_plus_b_equals_c": score,
                "can_transpose_terms": score,
                "can_divide_by_coefficient": score,
                "can_handle_negative_numbers": score,
                "can_handle_fractions": score,
            }
        },
        "error_tendency": [],
        "misconceptions": ["sign change"] if score < 45 else [],
        "learning_speed": "medium",
        "personality": {"response_style": "test"},
        "big_five": {
            "openness": "medium",
            "conscientiousness": "medium",
            "extraversion": "medium",
            "agreeableness": "medium",
            "neuroticism": "low",
        },
        "self_efficacy": self_efficacy,
        "question_tendency": "low",
        "motivation": "medium",
        "learning_history": [],
    }


def write_class(classes_dir, class_state: dict) -> None:
    classes_dir.mkdir(parents=True, exist_ok=True)
    path = classes_dir / f"{class_state['class_id']}.json"
    path.write_text(json.dumps(class_state, ensure_ascii=False), encoding="utf-8")


def test_loads_students_and_summarizes_class(tmp_path):
    students_dir = tmp_path / "students"
    classes_dir = tmp_path / "classes"
    state_manager = StateManager(students_dir)
    state_manager.save_student(make_student("S101", 30, "low"))
    state_manager.save_student(make_student("S102", 70, "high"))

    write_class(
        classes_dir,
        {
            "class_id": "class_test",
            "student_ids": ["S101", "S102"],
            "class_features": {"understanding_profile": "mixed"},
            "tags": ["unit_test"],
        },
    )

    manager = ClassManager(classes_dir=classes_dir, students_dir=students_dir)
    summary = manager.summarize_class("class_test")

    assert summary["student_count"] == 2
    assert summary["average_score"] == 50
    assert summary["low_score_students"] == ["S101"]
    assert summary["high_score_students"] == ["S102"]
    assert summary["trait_counts"]["self_efficacy"]["low"] == 1
    assert summary["trait_counts"]["self_efficacy"]["high"] == 1
    assert summary["misconception_students"] == ["S101"]


def test_rejects_duplicate_student_ids(tmp_path):
    manager = ClassManager(classes_dir=tmp_path / "classes", students_dir=tmp_path / "students")

    with pytest.raises(ClassDefinitionError, match="duplicates"):
        manager.validate_class(
            {
                "class_id": "bad_class",
                "student_ids": ["S001", "S001"],
                "class_features": {},
            }
        )


def test_repository_class_definitions_load():
    manager = ClassManager()

    class_ids = manager.list_classes()
    assert "class_3_basic" in class_ids
    assert "class_20_mixed" in class_ids

    summary = manager.summarize_class("class_20_mixed")
    assert summary["student_count"] == 20
    assert len(summary["student_ids"]) == 20
    assert summary["class_features"]["size"] == 20
