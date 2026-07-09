from fractions import Fraction

from src.grader import LinearEquationGrader, extract_x_value


def test_extract_x_value_from_answer_text():
    assert extract_x_value("答え: x = 4") == Fraction(4)
    assert extract_x_value("x=-3 です") == Fraction(-3)
    assert extract_x_value("答え: x = 1/2") == Fraction(1, 2)


def test_linear_equation_grader_marks_correct_answer():
    grader = LinearEquationGrader()

    result = grader.grade("x = 4", "途中式は省略します。答え: x = 4")

    assert result["is_correct"] is True
    assert result["score"] == 1


def test_linear_equation_grader_marks_incorrect_answer():
    grader = LinearEquationGrader()

    result = grader.grade("x = 4", "答え: x = 5")

    assert result["is_correct"] is False
    assert result["score"] == 0
