import pytest

from src.state_manager import StateManager, StudentStateError


def sample_student_state():
    return {
        "student_id": "S999",
        "name": "Test",
        "understanding": {"linear_equation": "basic"},
        "knowledge_state": {
            "linear_equation": {
                "level": "basic",
                "can_solve_ax_plus_b_equals_c": True,
            }
        },
        "error_tendency": [],
        "misconceptions": [],
        "learning_speed": "normal",
        "personality": {"confidence": "medium"},
        "big_five": {
            "openness": "medium",
            "conscientiousness": "medium",
            "extraversion": "medium",
            "agreeableness": "medium",
            "neuroticism": "medium",
        },
        "self_efficacy": "medium",
        "question_tendency": "medium",
        "motivation": "medium",
        "learning_history": [],
    }


def test_load_and_validate_student(tmp_path):
    students_dir = tmp_path / "students"
    manager = StateManager(students_dir)
    state = sample_student_state()

    manager.save_student(state)
    loaded = manager.load_student("S999")

    assert loaded["student_id"] == "S999"
    assert loaded["understanding"]["linear_equation"] == "basic"


def test_validate_student_rejects_missing_fields():
    with pytest.raises(StudentStateError):
        StateManager.validate_student({"student_id": "S999"})


def test_update_learning_history(tmp_path):
    students_dir = tmp_path / "students"
    manager = StateManager(students_dir)
    manager.save_student(sample_student_state())

    updated = manager.update_learning_history("S999", {"problem": "x+1=2"})

    assert updated["learning_history"] == [{"problem": "x+1=2"}]
