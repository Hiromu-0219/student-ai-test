from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.assessment_logger import AssessmentLogger
from src.grader import LinearEquationGrader
from src.student_ai import StudentAISimulator
from src.test_bank import TestBank


class TestRunner:
    __test__ = False

    def __init__(
        self,
        *,
        simulator: StudentAISimulator,
        test_bank: TestBank | None = None,
        grader: LinearEquationGrader | None = None,
        assessment_logger: AssessmentLogger | None = None,
    ) -> None:
        self.simulator = simulator
        self.test_bank = test_bank or TestBank()
        self.grader = grader or LinearEquationGrader()
        self.assessment_logger = assessment_logger or AssessmentLogger()

    def run_test(
        self,
        *,
        student_id: str,
        test_id: str,
        update_knowledge: bool = False,
    ) -> dict[str, Any]:
        if update_knowledge:
            raise NotImplementedError("Assessment-driven knowledge updates are intentionally disabled.")

        test_data = self.test_bank.load_test(test_id)
        question_results = []
        skill_totals: dict[str, int] = defaultdict(int)
        skill_correct: dict[str, int] = defaultdict(int)

        for question in test_data["questions"]:
            response = self.simulator.respond(
                student_id,
                question["problem"],
                update_knowledge=False,
            )
            grading = self.grader.grade(question["answer"], response["answer"])
            skill = question["skill"]
            skill_totals[skill] += 1
            skill_correct[skill] += grading["score"]
            question_results.append(
                {
                    "question_id": question["question_id"],
                    "problem": question["problem"],
                    "expected_answer": question["answer"],
                    "skill": skill,
                    "difficulty": question["difficulty"],
                    "student_answer": response["answer"],
                    "grading": grading,
                }
            )

        total_count = len(question_results)
        correct_count = sum(item["grading"]["score"] for item in question_results)
        skill_scores = {
            skill: round((skill_correct[skill] / total) * 100, 1)
            for skill, total in skill_totals.items()
        }
        result = {
            "student_id": student_id,
            "test_id": test_data["test_id"],
            "title": test_data["title"],
            "domain": test_data["domain"],
            "score_percentage": round((correct_count / total_count) * 100, 1),
            "correct_count": correct_count,
            "total_count": total_count,
            "skill_scores": skill_scores,
            "question_results": question_results,
            "updates_knowledge": False,
        }
        return self.assessment_logger.log_assessment(result)
