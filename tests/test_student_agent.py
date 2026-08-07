from src.student_agent import StudentAgent, normalize_student_turn


def test_normalize_student_turn_removes_teacher_dialogue():
    raw = """生徒：まず3を引いて、2x = 8にします。答え: x = 4

教師：次は確認問題です。
生徒：もう一問やります。"""

    result = normalize_student_turn(raw)

    assert "教師" not in result
    assert "もう一問" not in result
    assert result.startswith("まず3を引いて")
    assert "答え: x = 4" in result


def test_normalize_student_turn_skips_leading_teacher_line_and_keeps_student_line():
    raw = """教師：2x + 3 = 11 を解いてください。

生徒：まず3を両辺から引くと、2x = 8です。答え: x = 4"""

    result = normalize_student_turn(raw)

    assert "教師" not in result
    assert "生徒" not in result
    assert result == "まず3を両辺から引くと、2x = 8です。 答え: x = 4"


def test_normalize_assessment_keeps_answer_line_only():
    raw = """途中式です。答え: x = 4
教師：解説します。"""

    assert normalize_student_turn(raw, assessment=True) == "答え: x = 4"


def test_normalize_student_turn_adds_x_to_numeric_answer_label():
    raw = "両辺を2で割ります。答え: 4"

    assert normalize_student_turn(raw) == "両辺を2で割ります。 答え: x = 4"


def test_normalize_student_turn_fills_linear_equation_answer_from_teacher_message():
    raw = "3をどう扱うかを考えています。"

    result = normalize_student_turn(raw, teacher_message="3x = 15 を解いてください。")

    assert result.endswith("答え: x = 5")


def test_normalize_student_turn_converts_empty_to_unknown_answer():
    assert normalize_student_turn("   ") == "答え: わかりません"


class _FakeGenerator:
    model_id = "fake"

    def __init__(self, answer):
        self.answer = answer

    def generate(self, system_prompt, user_prompt):
        return self.answer


def test_lesson_probe_forces_controlled_answer_label():
    agent = StudentAgent(
        _FakeGenerator("まず3を引いて、2で割ります。答え: x = 4")
    )

    result = agent.answer(
        {
            "student_id": "S999",
            "knowledge_state": {"linear_equation": {"score": 30}},
            "misconceptions": [],
            "self_efficacy": "medium",
            "question_tendency": "medium",
            "motivation": "medium",
        },
        "2x + 3 = 11 を解いてください。",
        assessment_directive={
            "mode": "lesson_probe",
            "target_correct": False,
            "correct_probability": 20,
            "target_answer": "x = 5",
            "rationale": "controlled wrong answer",
        },
    )

    assert result.endswith("答え: x = 5")
    assert "答え: x = 4" not in result



def test_student_agent_removes_solution_when_behavior_says_listen():
    agent = StudentAgent(
        _FakeGenerator("3x = 15 なので、両辺を3で割ります。答え: x = 5")
    )

    result = agent.answer(
        {
            "student_id": "S999",
            "knowledge_state": {"linear_equation": {"score": 80}},
            "misconceptions": [],
            "self_efficacy": "medium",
            "question_tendency": "medium",
            "motivation": "medium",
        },
        "今日の目標は係数で両辺を割ることです。まず確認しましょう。",
    )

    assert "答え" not in result
    assert "x =" not in result
    assert result
