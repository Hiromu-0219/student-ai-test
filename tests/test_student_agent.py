from src.student_agent import normalize_student_turn


def test_normalize_student_turn_removes_teacher_dialogue():
    raw = """生徒：まず3を引いて、2x = 8にします。
答え: x = 4

教師：次は確認問題です。
生徒：もう一問やります。
"""

    result = normalize_student_turn(raw)

    assert "教師" not in result
    assert "もう一問" not in result
    assert result.startswith("まず3を引いて")
    assert "答え: x = 4" in result


def test_normalize_assessment_keeps_answer_line_only():
    raw = """途中式です。
答え: x = 4
教師：解説します。
"""

    assert normalize_student_turn(raw, assessment=True) == "答え: x = 4"
