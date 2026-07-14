from __future__ import annotations

from typing import Any


class RuleBasedTeacherUtteranceBuilder:
    """Turns an intervention plan into concrete teacher utterances.

    This is deliberately rule-based for now. The plan decides what to do; this
    class only renders it into classroom-ready wording.
    """

    def build(self, intervention_plan: dict[str, Any]) -> dict[str, Any]:
        whole_class_plan = intervention_plan.get("whole_class_plan", {})
        individual_supports = intervention_plan.get("individual_supports", [])
        whole_class_utterance = self._whole_class_utterance(whole_class_plan)
        individual_utterances = [
            self._individual_utterance(support) for support in individual_supports
        ]
        return {
            "whole_class_utterance": whole_class_utterance,
            "individual_utterances": individual_utterances,
            "next_problem": whole_class_plan.get("next_problem"),
            "expected_answer": whole_class_plan.get("expected_answer"),
            "source_plan": intervention_plan,
        }

    def _whole_class_utterance(self, plan: dict[str, Any]) -> str:
        focus = plan.get("focus") or "一次方程式の解き方"
        teacher_move = plan.get("teacher_move") or "次の問題を確認する"
        next_problem = plan.get("next_problem")
        pace = plan.get("pace")

        if pace == "slow_down":
            opening = "ここで一度、全体で確認します。"
        elif pace == "maintain_or_raise":
            opening = "次は少し自分で考える時間を取ります。"
        else:
            opening = "今の流れを保ちながら確認します。"

        problem_part = f" 次の問題は {next_problem} です。" if next_problem else ""
        return f"{opening}{focus}を見ます。{teacher_move}。{problem_part}".strip()

    def _individual_utterance(self, support: dict[str, Any]) -> dict[str, str]:
        student_id = str(support.get("student_id", "UNKNOWN"))
        support_type = support.get("support_type", "support")
        target_skill = support.get("target_skill", "linear_equation")

        if support_type == "confidence_support":
            utterance = (
                f"{student_id}さん、考えようとしている点は大事です。"
                "まず1つだけ確認しましょう。どの操作で迷いましたか。"
            )
        elif support_type == "micro_practice":
            utterance = (
                f"{student_id}さん、同じ形を小さく確認します。"
                "途中式を1行だけ書いて、次の一手を見せてください。"
            )
        elif support_type == "misconception_check":
            utterance = (
                f"{student_id}さん、間違いやすいところを一緒に確認します。"
                "反対側へ移すとき、符号がどう変わるかだけ見ましょう。"
            )
        elif support_type == "extension":
            utterance = (
                f"{student_id}さん、今の問題はよくできています。"
                "少し数値を変えた問題で、解き方を短く説明してみましょう。"
            )
        else:
            utterance = f"{student_id}さん、今の考え方をもう少し聞かせてください。"

        return {
            "student_id": student_id,
            "support_type": str(support_type),
            "target_skill": str(target_skill),
            "utterance": utterance,
            "reason": str(support.get("reason", "")),
        }
