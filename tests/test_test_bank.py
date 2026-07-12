from src.test_bank import TestBank


def test_linear_equation_20q_test_has_twenty_questions():
    test_data = TestBank().load_test("linear_equation_20q_001")

    assert test_data["test_id"] == "linear_equation_20q_001"
    assert len(test_data["questions"]) == 20
