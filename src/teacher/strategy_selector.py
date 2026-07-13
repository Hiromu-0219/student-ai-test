from __future__ import annotations

from typing import Any


class RuleBasedTeachingStrategySelector:
    """Selects a teaching strategy from explicit student state and observation.

    This class is intentionally deterministic. The LLM can later generate richer
    wording, but the instructional decision is kept inspectable for experiments.
    """

    def select_strategy(self, context: dict[str, Any]) -> dict[str, Any]:
        summary = context.get("student_state_summary", {})
        observation = context.get("communication_ai_observation", {})
        traits = _merged_traits(summary, observation)
        target_skill = context.get("target_skill", "can_solve_ax_plus_b_equals_c")
        skill_score = _score(summary.get("knowledge_state", {}).get(target_skill, 0))
        misconceptions = summary.get("misconceptions", [])

        strategies = self._choose_strategies(
            target_skill=target_skill,
            skill_score=skill_score,
            traits=traits,
            misconceptions=misconceptions,
            context=context,
        )
        teacher_utterance = self._build_teacher_utterance(
            target_skill=target_skill,
            skill_score=skill_score,
            traits=traits,
            context=context,
        )
        next_problem = self._select_next_problem(context, target_skill)

        return {
            "target_skill": target_skill,
            "diagnosis": self._diagnosis(target_skill, skill_score, traits, misconceptions),
            "selected_strategies": strategies,
            "teacher_utterance": teacher_utterance,
            "next_problem": next_problem.get("problem"),
            "expected_answer": next_problem.get("answer"),
            "reason": self._reason(strategies, traits, observation),
        }

    def _choose_strategies(
        self,
        *,
        target_skill: str,
        skill_score: int,
        traits: dict[str, str],
        misconceptions: list[str],
        context: dict[str, Any],
    ) -> list[str]:
        strategies: list[str] = []
        if traits.get("self_efficacy") in {"very_low", "low"} or traits.get("neuroticism") in {
            "high",
            "very_high",
        }:
            strategies.append("encouragement")
        if skill_score < 40:
            strategies.append("worked_example")
        if _has_matching_misconception(target_skill, misconceptions, context):
            strategies.append("misconception_confrontation")
        if traits.get("conscientiousness") in {"very_low", "low"}:
            strategies.append("micro_practice")
        if target_skill in {"can_transpose_terms", "can_divide_by_coefficient"}:
            strategies.append("guided_question")
        if skill_score >= 75:
            strategies.append("answer_check")
        if not strategies:
            strategies.append("guided_question")
        return _unique(strategies)[:4]

    def _build_teacher_utterance(
        self,
        *,
        target_skill: str,
        skill_score: int,
        traits: dict[str, str],
        context: dict[str, Any],
    ) -> str:
        needs_support = traits.get("self_efficacy") in {"very_low", "low"}
        prefix = "迷っている点を言えたのは大事です。 " if needs_support else ""
        if target_skill == "can_transpose_terms":
            text = prefix + "移項では、反対側へ移した項の符号はどう変わりますか。まずそこだけ確認しましょう。"
        elif target_skill == "can_divide_by_coefficient":
            text = prefix + "3x = 15 のような式では、x だけにするために両辺を何で割ればよいですか。"
        elif target_skill == "can_handle_negative_numbers":
            text = prefix + "負の符号を残したまま、係数と定数を分けて見ましょう。最後に符号を確認します。"
        elif target_skill == "can_handle_fractions":
            text = prefix + "分数があるときは、先に分母を払えるかを考えます。両辺に同じ数をかけてみましょう。"
        else:
            text = prefix + "まず定数項を移項し、そのあと係数で割る順番で解いてみましょう。"

        if skill_score < 25:
            text += " 例題を一緒に1問だけ確認してから、同じ形を解きます。"
        return _truncate(text, context.get("constraints", {}).get("max_teacher_utterance_chars", 120))

    def _select_next_problem(self, context: dict[str, Any], target_skill: str) -> dict[str, Any]:
        bank = context.get("next_problem_bank", {})
        problems = bank.get(target_skill) or bank.get("can_solve_ax_plus_b_equals_c") or []
        return problems[0] if problems else {"problem": None, "answer": None}

    def _diagnosis(
        self,
        target_skill: str,
        skill_score: int,
        traits: dict[str, str],
        misconceptions: list[str],
    ) -> str:
        return (
            f"{target_skill} のスコアは {skill_score}/100。"
            f"自己効力感={traits.get('self_efficacy', 'unknown')}、"
            f"質問傾向={traits.get('question_tendency', 'unknown')}。"
            f"誤概念は {len(misconceptions)} 件記録されています。"
        )

    def _reason(
        self,
        strategies: list[str],
        traits: dict[str, str],
        observation: dict[str, Any],
    ) -> str:
        attention = observation.get("recommended_teacher_attention", [])
        base = f"選択理由: {', '.join(strategies)}。"
        if attention:
            base += f" 伝達AIの注意点: {attention[0]}"
        elif traits:
            base += " 生徒状態と発話推定に基づき、次の一手を短く絞りました。"
        return base


def _merged_traits(summary: dict[str, Any], observation: dict[str, Any]) -> dict[str, str]:
    traits = {
        "self_efficacy": summary.get("self_efficacy", "medium"),
        "question_tendency": summary.get("question_tendency", "medium"),
        "motivation": summary.get("motivation", "medium"),
        "conscientiousness": summary.get("big_five", {}).get("conscientiousness", "medium"),
        "neuroticism": summary.get("big_five", {}).get("neuroticism", "medium"),
        "extraversion": summary.get("big_five", {}).get("extraversion", "medium"),
    }
    observed_traits = observation.get("trait_estimates", {})
    for key, value in observed_traits.items():
        if key in traits and value:
            traits[key] = value
    return traits


def _has_matching_misconception(
    target_skill: str,
    misconceptions: list[str],
    context: dict[str, Any],
) -> bool:
    keywords = context.get("misconception_map", {}).get(target_skill, [])
    if not keywords:
        return bool(misconceptions)
    joined = "\n".join(misconceptions)
    return any(keyword in joined for keyword in keywords)


def _score(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, min(100, value))
    return 0


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "…"
