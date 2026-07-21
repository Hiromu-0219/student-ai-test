from __future__ import annotations

import json
import re
from typing import Any


class RuleBasedTeacherUtteranceBuilder:
    """Turn an intervention plan into concrete teacher utterances."""

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
                "反対側へ移すとき、符号がどう変わるかを見ましょう。"
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


TEACHER_UTTERANCE_SYSTEM_PROMPT = """You generate concise Japanese teacher utterances for an education simulation.
Return one valid JSON object only. Do not use Markdown.
The teacher must not mention hidden student parameters directly.
"""


class LLMTeacherUtteranceBuilder:
    """Render teacher utterances with an LLM and rule-based fallback."""

    def __init__(
        self,
        text_generator: Any,
        *,
        fallback: RuleBasedTeacherUtteranceBuilder | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or RuleBasedTeacherUtteranceBuilder()

    def build(self, intervention_plan: dict[str, Any]) -> dict[str, Any]:
        fallback_result = self.fallback.build(intervention_plan)
        prompt = _build_teacher_utterance_prompt(intervention_plan, fallback_result)
        raw_output = self.text_generator.generate(
            TEACHER_UTTERANCE_SYSTEM_PROMPT,
            prompt,
        )
        parsed = _parse_json_object(raw_output)
        if parsed is None:
            return {**fallback_result, "generation_mode": "rule_based_fallback"}

        return {
            "whole_class_utterance": str(
                parsed.get("whole_class_utterance")
                or fallback_result["whole_class_utterance"]
            ),
            "individual_utterances": _normalize_individual_utterances(
                parsed.get("individual_utterances"),
                fallback_result["individual_utterances"],
            ),
            "next_problem": fallback_result.get("next_problem"),
            "expected_answer": fallback_result.get("expected_answer"),
            "source_plan": intervention_plan,
            "generation_mode": "llm",
        }


def _build_teacher_utterance_prompt(
    intervention_plan: dict[str, Any],
    fallback_result: dict[str, Any],
) -> str:
    whole_class_plan = intervention_plan.get("whole_class_plan", {})
    individual_supports = intervention_plan.get("individual_supports", [])
    compact_plan = {
        "lesson_goal": intervention_plan.get("lesson_goal", {}),
        "whole_class_plan": whole_class_plan,
        "individual_supports": individual_supports,
    }
    required_students = [
        str(item.get("student_id", "UNKNOWN")) for item in individual_supports
    ]
    fallback_compact = {
        "whole_class_utterance": fallback_result.get("whole_class_utterance"),
        "individual_utterances": fallback_result.get("individual_utterances", []),
    }
    return f"""Create classroom-ready Japanese utterances.

Plan:
{json.dumps(compact_plan, ensure_ascii=False, indent=2)}

Reference wording if needed:
{json.dumps(fallback_compact, ensure_ascii=False, indent=2)}

Required student_ids: {json.dumps(required_students, ensure_ascii=False)}

Return exactly this JSON shape:
{{
  "whole_class_utterance": "全体向けの短い教師発話",
  "individual_utterances": [
    {{
      "student_id": "S001",
      "support_type": "micro_practice",
      "target_skill": "can_transpose_terms",
      "utterance": "個別向けの短い教師発話",
      "reason": "短い理由"
    }}
  ]
}}"""


def _parse_json_object(raw_output: str) -> dict[str, Any] | None:
    text = raw_output.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_individual_utterances(
    value: Any,
    fallback: list[dict[str, str]],
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return fallback

    fallback_by_student = {item["student_id"]: item for item in fallback}
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        student_id = str(item.get("student_id", "")).strip()
        if not student_id:
            continue
        fallback_item = fallback_by_student.get(student_id, {})
        normalized.append(
            {
                "student_id": student_id,
                "support_type": str(
                    item.get("support_type")
                    or fallback_item.get("support_type")
                    or "support"
                ),
                "target_skill": str(
                    item.get("target_skill")
                    or fallback_item.get("target_skill")
                    or "linear_equation"
                ),
                "utterance": str(
                    item.get("utterance")
                    or fallback_item.get("utterance")
                    or ""
                ),
                "reason": str(item.get("reason") or fallback_item.get("reason") or ""),
            }
        )

    return normalized or fallback
