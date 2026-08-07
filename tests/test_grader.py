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



def test_extract_x_value_from_natural_language_answer():
    assert extract_x_value("答えは4です。") == Fraction(4)
    assert extract_x_value("x は 4 になります。") == Fraction(4)
    assert extract_x_value("xの値は-3です。") == Fraction(-3)
    assert extract_x_value("the answer is 1/2") == Fraction(1, 2)
    assert extract_x_value("x equals 5") == Fraction(5)


def test_extract_x_value_uses_final_x_value_not_intermediate_step():
    text = "まず3を引くと、2x = 8 になります。その後、両辺を2で割るので x = 4 です。"
    assert extract_x_value(text) == Fraction(4)


def test_extract_x_value_does_not_treat_coefficient_equation_as_answer():
    assert extract_x_value("まず3を引くと、2x = 8 になります。") is None
