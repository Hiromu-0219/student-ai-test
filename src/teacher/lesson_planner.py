from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


class RuleBasedLessonPlanner:
    """Plan a whole lesson from class-level teacher beliefs.

    This class decides the lesson goal and phase structure. It does not generate
    final teacher utterances; that is handled by utterance builders.
    """

    def build_class_profile(
        self,
        teacher_beliefs: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        if not teacher_beliefs:
            return {
                "student_count": 0,
                "average_estimated_score": 50.0,
                "score_std": 0.0,
                "low_score_students": [],
                "high_score_students": [],
                "trait_counts": {},
                "common_misconceptions": [],
                "common_risks": ["観察済みの生徒情報が少ない"],
            }

        scores = {
            student_id: _estimated_score(belief)
            for student_id, belief in teacher_beliefs.items()
        }
        trait_counts = _trait_counts(teacher_beliefs)
        common_misconceptions = _common_misconceptions(teacher_beliefs)
        low_score_students = [
            student_id for student_id, score in scores.items() if score < 45
        ]
        high_score_students = [
            student_id for student_id, score in scores.items() if score >= 65
        ]
        score_values = list(scores.values())

        return {
            "student_count": len(teacher_beliefs),
            "average_estimated_score": round(mean(score_values), 1),
            "score_std": round(pstdev(score_values), 1) if len(score_values) > 1 else 0.0,
            "low_score_students": low_score_students,
            "high_score_students": high_score_students,
            "trait_counts": trait_counts,
            "common_misconceptions": common_misconceptions,
            "common_risks": _common_risks(
                low_score_students=low_score_students,
                trait_counts=trait_counts,
                common_misconceptions=common_misconceptions,
            ),
        }

    def plan_lesson(
        self,
        *,
        teacher_beliefs: dict[str, dict[str, Any]],
        curriculum: dict[str, Any],
        total_minutes: int = 30,
    ) -> dict[str, Any]:
        class_profile = self.build_class_profile(teacher_beliefs)
        lesson_goal = self._select_lesson_goal(class_profile, curriculum)
        target_skill = lesson_goal.get("target_skill", "can_solve_ax_plus_b_equals_c")
        lesson_structure = self._lesson_structure(
            class_profile=class_profile,
            lesson_goal=lesson_goal,
            total_minutes=total_minutes,
            curriculum=curriculum,
        )
        return {
            "lesson_goal": lesson_goal,
            "class_profile": class_profile,
            "lesson_structure": lesson_structure,
            "individual_support_policy": self._individual_support_policy(
                teacher_beliefs,
                target_skill,
            ),
            "reason": self._reason(class_profile, lesson_goal),
        }

    def _select_lesson_goal(
        self,
        class_profile: dict[str, Any],
        curriculum: dict[str, Any],
    ) -> dict[str, Any]:
        misconception_text = " ".join(
            item["name"] for item in class_profile.get("common_misconceptions", [])
        )
        if any(token in misconception_text for token in ["係数", "割る", "3x"]):
            return _goal_for_skill(curriculum, "can_divide_by_coefficient")
        if any(token in misconception_text for token in ["移項", "符号"]):
            return _goal_for_skill(curriculum, "can_transpose_terms")

        student_count = max(1, int(class_profile.get("student_count", 1)))
        low_count = len(class_profile.get("low_score_students", []))
        if low_count / student_count >= 0.5:
            return _goal_for_skill(curriculum, "can_transpose_terms")
        if class_profile.get("average_estimated_score", 50) < 45:
            return _goal_for_skill(curriculum, "can_transpose_terms")
        return _goal_for_skill(curriculum, "can_divide_by_coefficient")

    def _lesson_structure(
        self,
        *,
        class_profile: dict[str, Any],
        lesson_goal: dict[str, Any],
        total_minutes: int,
        curriculum: dict[str, Any],
    ) -> list[dict[str, Any]]:
        total_minutes = max(15, total_minutes)
        low_count = len(class_profile.get("low_score_students", []))
        student_count = max(1, int(class_profile.get("student_count", 1)))
        low_ratio = low_count / student_count
        target_skill = lesson_goal.get("target_skill", "can_solve_ax_plus_b_equals_c")
        problems = curriculum.get("next_problem_bank", {}).get(target_skill, [])
        first_problem = problems[0] if problems else {"problem": None, "answer": None}
        second_problem = problems[1] if len(problems) > 1 else first_problem

        if low_ratio >= 0.5:
            allocation = [3, 8, 6, 8, 5]
        elif class_profile.get("score_std", 0) >= 12:
            allocation = [3, 6, 5, 10, 6]
        else:
            allocation = [3, 5, 5, 11, 6]
        allocation = _scale_minutes(allocation, total_minutes)

        return [
            {
                "phase": "導入",
                "minutes": allocation[0],
                "purpose": "前回の反応を短く振り返り、今日の目標を共有する",
            },
            {
                "phase": "全体説明",
                "minutes": allocation[1],
                "purpose": lesson_goal.get("goal_text", "一次方程式の基本操作を確認する"),
            },
            {
                "phase": "例題",
                "minutes": allocation[2],
                "problem": first_problem.get("problem"),
                "expected_answer": first_problem.get("answer"),
                "purpose": "教師と一緒に1手ずつ確認する",
            },
            {
                "phase": "個別演習",
                "minutes": allocation[3],
                "purpose": "生徒ごとのつまずきを観察し、必要な個別支援を入れる",
            },
            {
                "phase": "確認",
                "minutes": allocation[4],
                "problem": second_problem.get("problem"),
                "expected_answer": second_problem.get("answer"),
                "purpose": "授業目標がどの程度達成されたかを確認する",
            },
        ]

    def _individual_support_policy(
        self,
        teacher_beliefs: dict[str, dict[str, Any]],
        target_skill: str,
    ) -> list[dict[str, str]]:
        policies = []
        for student_id, belief in sorted(teacher_beliefs.items()):
            traits = belief.get("estimated_traits", {})
            score = _estimated_score(belief)
            if _trait_level(traits, "self_efficacy") == "low":
                policy = "自信を下げない声かけを優先し、途中式を1行だけ確認する"
            elif _trait_level(traits, "question_tendency") == "low":
                policy = "教師側から小さな確認質問を入れる"
            elif score < 45:
                policy = "同じ型の小問を使い、操作を1つずつ確認する"
            elif score >= 65:
                policy = "発展問題や説明役を任せ、理解を言語化させる"
            else:
                policy = "全体演習中の反応を継続観察する"
            policies.append(
                {
                    "student_id": student_id,
                    "target_skill": target_skill,
                    "policy": policy,
                }
            )
        return policies

    def _reason(
        self,
        class_profile: dict[str, Any],
        lesson_goal: dict[str, Any],
    ) -> str:
        return (
            f"クラス平均推定理解度={class_profile.get('average_estimated_score')}、"
            f"低理解層={len(class_profile.get('low_score_students', []))}人、"
            f"主なリスク={class_profile.get('common_risks', [])}。"
            f"そのため授業目標を「{lesson_goal.get('goal_text')}」に設定。"
        )


def _estimated_score(belief: dict[str, Any]) -> int:
    return int(
        belief.get("estimated_knowledge", {})
        .get("linear_equation", {})
        .get("score", 50)
    )


def _trait_level(traits: dict[str, Any], key: str) -> str:
    value = traits.get(key, {})
    if isinstance(value, dict):
        return str(value.get("level", "medium"))
    return str(value or "medium")


def _trait_counts(teacher_beliefs: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    keys = ["self_efficacy", "question_tendency", "motivation", "neuroticism"]
    counts = {key: {"low": 0, "medium": 0, "high": 0} for key in keys}
    for belief in teacher_beliefs.values():
        traits = belief.get("estimated_traits", {})
        for key in keys:
            level = _trait_level(traits, key)
            if level in counts[key]:
                counts[key][level] += 1
    return counts


def _common_misconceptions(
    teacher_beliefs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for belief in teacher_beliefs.values():
        for item in belief.get("estimated_misconceptions", []):
            name = str(item.get("name", ""))
            if not name:
                continue
            current = grouped.setdefault(
                name,
                {"name": name, "student_count": 0, "max_confidence": 0.0},
            )
            current["student_count"] += 1
            current["max_confidence"] = max(
                float(current["max_confidence"]),
                float(item.get("confidence", 0.0)),
            )
    return sorted(
        grouped.values(),
        key=lambda row: (row["student_count"], row["max_confidence"]),
        reverse=True,
    )


def _common_risks(
    *,
    low_score_students: list[str],
    trait_counts: dict[str, dict[str, int]],
    common_misconceptions: list[dict[str, Any]],
) -> list[str]:
    risks = []
    if low_score_students:
        risks.append("推定理解度が低い生徒がいる")
    if trait_counts.get("self_efficacy", {}).get("low", 0) >= 2:
        risks.append("自己効力感が低い生徒が複数いる")
    if trait_counts.get("question_tendency", {}).get("low", 0) >= 2:
        risks.append("質問しにくい生徒が複数いる")
    if trait_counts.get("neuroticism", {}).get("high", 0) >= 2:
        risks.append("不安が高い生徒が複数いる")
    if common_misconceptions:
        risks.append(f"共通誤概念: {common_misconceptions[0]['name']}")
    return risks or ["大きな共通リスクはまだ観察されていない"]


def _goal_for_skill(curriculum: dict[str, Any], target_skill: str) -> dict[str, Any]:
    for goal in curriculum.get("lesson_goals", []):
        if goal.get("target_skill") == target_skill:
            return goal
    return {
        "goal_id": target_skill,
        "target_skill": target_skill,
        "goal_text": "一次方程式の理解を深める",
        "success_criteria": [],
    }


def _scale_minutes(base: list[int], total_minutes: int) -> list[int]:
    base_total = sum(base)
    scaled = [max(1, round(value * total_minutes / base_total)) for value in base]
    delta = total_minutes - sum(scaled)
    scaled[-1] += delta
    if scaled[-1] < 1:
        scaled[-2] += scaled[-1] - 1
        scaled[-1] = 1
    return scaled
