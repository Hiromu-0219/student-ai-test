from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol


LEVELS = ("low", "medium", "high")


COMMUNICATION_AI_SYSTEM_PROMPT = """あなたは教育シミュレーションの伝達AIです。
生徒AIの発話を観察し、先生AIに渡すために個人特徴を分類してください。

制約:
- 数学の正誤ではなく、発話スタイルから判断してください。
- 必ずJSONだけを返してください。
- Markdownや説明文をJSONの外に書かないでください。
- profile_prediction は A, B, C, D のいずれかです。
- trait_estimates の各値は low, medium, high のいずれかです。
"""


class TextGenerator(Protocol):
    model_id: str

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass


@dataclass(frozen=True)
class TraitClassification:
    profile_prediction: str
    trait_estimates: dict[str, str]
    evidence: list[str]
    confidence: float
    teacher_summary: str
    recommended_teacher_attention: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_prediction": self.profile_prediction,
            "trait_estimates": self.trait_estimates,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "teacher_summary": self.teacher_summary,
            "recommended_teacher_attention": self.recommended_teacher_attention,
        }


@dataclass(frozen=True)
class ClassroomCommunicationSummary:
    student_count: int
    individual_results: list[dict[str, Any]]
    profile_counts: dict[str, int]
    trait_level_counts: dict[str, dict[str, int]]
    priority_students: list[dict[str, Any]]
    classroom_summary: str
    recommended_teacher_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_count": self.student_count,
            "individual_results": self.individual_results,
            "profile_counts": self.profile_counts,
            "trait_level_counts": self.trait_level_counts,
            "priority_students": self.priority_students,
            "classroom_summary": self.classroom_summary,
            "recommended_teacher_actions": self.recommended_teacher_actions,
        }


class CommunicationAI:
    """Observer/communication layer between student AI and teacher AI.

    This first implementation is rule-based so experiments are deterministic.
    Later, the same public interface can call an LLM classifier.
    """

    def classify_utterance(
        self,
        *,
        utterance: str,
        student_id: str | None = None,
    ) -> TraitClassification:
        features = _extract_features(utterance)
        traits = _estimate_traits(features)
        profile = _predict_profile(traits, features)
        evidence = _evidence(features)
        confidence = _confidence(features, profile)
        teacher_summary = _teacher_summary(student_id, traits, evidence)
        attention = _recommended_teacher_attention(traits, features)
        return TraitClassification(
            profile_prediction=profile,
            trait_estimates=traits,
            evidence=evidence,
            confidence=confidence,
            teacher_summary=teacher_summary,
            recommended_teacher_attention=attention,
        )

    def classify_many(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for row in rows:
            classification = self.classify_utterance(
                utterance=row["answer"],
                student_id=row.get("student_id"),
            )
            results.append({**row, **classification.to_dict()})
        return results

    def summarize_classroom(
        self,
        rows: list[dict[str, Any]],
        *,
        min_students: int = 3,
        max_students: int = 20,
    ) -> ClassroomCommunicationSummary:
        _validate_classroom_size(rows, min_students, max_students)
        individual_results = self.classify_many(rows)
        profile_counts = _count_profiles(individual_results)
        trait_level_counts = _count_trait_levels(individual_results)
        priority_students = _select_priority_students(individual_results)
        actions = _classroom_actions(
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
        )
        summary = _classroom_summary_text(
            student_count=len(individual_results),
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
        )
        return ClassroomCommunicationSummary(
            student_count=len(individual_results),
            individual_results=individual_results,
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
            classroom_summary=summary,
            recommended_teacher_actions=actions,
        )


class LLMCommunicationAI:
    """LLM-based communication AI with rule-based fallback."""

    def __init__(
        self,
        text_generator: TextGenerator,
        *,
        fallback: CommunicationAI | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or CommunicationAI()

    def classify_utterance(
        self,
        *,
        utterance: str,
        student_id: str | None = None,
    ) -> TraitClassification:
        fallback_result = self.fallback.classify_utterance(
            utterance=utterance,
            student_id=student_id,
        )
        prompt = _build_llm_classification_prompt(
            utterance=utterance,
            student_id=student_id,
            fallback_result=fallback_result,
        )
        raw_output = self.text_generator.generate(
            COMMUNICATION_AI_SYSTEM_PROMPT,
            prompt,
        )
        parsed = _parse_llm_classification(raw_output)
        if parsed is None:
            return fallback_result

        traits = _normalize_traits(parsed.get("trait_estimates", {}), fallback_result.trait_estimates)
        profile = _normalize_profile(
            parsed.get("profile_prediction"),
            fallback_result.profile_prediction,
        )
        evidence = _normalize_string_list(parsed.get("evidence"), fallback_result.evidence)
        attention = _normalize_string_list(
            parsed.get("recommended_teacher_attention"),
            fallback_result.recommended_teacher_attention,
        )
        teacher_summary = str(parsed.get("teacher_summary") or fallback_result.teacher_summary)
        confidence = _normalize_confidence(parsed.get("confidence"), fallback_result.confidence)

        return TraitClassification(
            profile_prediction=profile,
            trait_estimates=traits,
            evidence=evidence,
            confidence=confidence,
            teacher_summary=teacher_summary,
            recommended_teacher_attention=attention,
        )

    def classify_many(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for row in rows:
            classification = self.classify_utterance(
                utterance=row["answer"],
                student_id=row.get("student_id"),
            )
            results.append({**row, **classification.to_dict()})
        return results

    def summarize_classroom(
        self,
        rows: list[dict[str, Any]],
        *,
        min_students: int = 3,
        max_students: int = 20,
    ) -> ClassroomCommunicationSummary:
        _validate_classroom_size(rows, min_students, max_students)
        fallback_summary = self.fallback.summarize_classroom(
            rows,
            min_students=min_students,
            max_students=max_students,
        )
        individual_results = self.classify_many(rows)
        profile_counts = _count_profiles(individual_results)
        trait_level_counts = _count_trait_levels(individual_results)
        priority_students = _select_priority_students(individual_results)
        actions = _classroom_actions(
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
        )
        summary = _classroom_summary_text(
            student_count=len(individual_results),
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
        )
        if not summary:
            summary = fallback_summary.classroom_summary
        return ClassroomCommunicationSummary(
            student_count=len(individual_results),
            individual_results=individual_results,
            profile_counts=profile_counts,
            trait_level_counts=trait_level_counts,
            priority_students=priority_students,
            classroom_summary=summary,
            recommended_teacher_actions=actions or fallback_summary.recommended_teacher_actions,
        )


def _extract_features(utterance: str) -> dict[str, bool | int]:
    text = utterance
    return {
        "has_low_confidence": any(token in text for token in ["自信はない", "たぶん", "かも", "不安"]),
        "has_high_confidence": any(token in text for token in ["分かります", "できます", "です。"]),
        "asks_question": any(token in text for token in ["ですか", "ますか", "合っていますか", "教えて"]),
        "shows_anxiety": any(token in text for token in ["不安", "迷", "自信はない", "確認"]),
        "shows_persistence": any(token in text for token in ["もう一度", "考えます", "やってみます", "間違っていたら"]),
        "shows_steps": any(token in text for token in ["まず", "それから", "移して", "係数", "両辺"]),
        "short_answer": len(text) <= 35,
        "talkative_answer": len(text) >= 75,
        "accepts_teacher": any(token in text for token in ["はい", "なるほど", "わかりました"]),
        "prefers_checking_sign": any(token in text for token in ["符号", "移項"]),
        "length": len(text),
    }


def _build_llm_classification_prompt(
    *,
    utterance: str,
    student_id: str | None,
    fallback_result: TraitClassification,
) -> str:
    return f"""分類対象:
- student_id: {student_id}
- utterance: {utterance}

候補プロファイル:
A. 自信低め・質問多め・不安強め
B. 丁寧・粘り強い・協調的
C. 短文・質問少なめ・そっけない
D. 自信あり・発話多め・新しい方法に前向き

推定する特徴:
- self_efficacy: low / medium / high
- question_tendency: low / medium / high
- motivation: low / medium / high
- extraversion: low / medium / high
- conscientiousness: low / medium / high
- neuroticism: low / medium / high

参考用のルールベース推定:
{json.dumps(fallback_result.to_dict(), ensure_ascii=False)}

次のJSON形式だけで返してください。
{{
  "profile_prediction": "A",
  "trait_estimates": {{
    "self_efficacy": "low",
    "question_tendency": "high",
    "motivation": "medium",
    "extraversion": "medium",
    "conscientiousness": "medium",
    "neuroticism": "high"
  }},
  "evidence": ["根拠1", "根拠2"],
  "confidence": 0.8,
  "teacher_summary": "先生AIに渡す短い要約",
  "recommended_teacher_attention": ["授業上の注意1", "授業上の注意2"]
}}"""


def _parse_llm_classification(raw_output: str) -> dict[str, Any] | None:
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


def _normalize_profile(value: Any, fallback: str) -> str:
    value = str(value).strip().upper()
    return value if value in {"A", "B", "C", "D"} else fallback


def _normalize_traits(values: Any, fallback: dict[str, str]) -> dict[str, str]:
    if not isinstance(values, dict):
        return fallback
    normalized = {}
    for key, fallback_value in fallback.items():
        value = str(values.get(key, fallback_value)).strip().lower()
        normalized[key] = value if value in LEVELS else fallback_value
    return normalized


def _normalize_string_list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        strings = [str(item) for item in value if str(item).strip()]
        return strings or fallback
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return fallback


def _normalize_confidence(value: Any, fallback: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return fallback
    return round(max(0.0, min(1.0, confidence)), 2)


def _validate_classroom_size(
    rows: list[dict[str, Any]],
    min_students: int,
    max_students: int,
) -> None:
    if not min_students <= len(rows) <= max_students:
        raise ValueError(
            f"classroom summary expects {min_students}-{max_students} students, "
            f"got {len(rows)}"
        )


def _count_profiles(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for result in results:
        profile = result.get("profile_prediction")
        if profile in counts:
            counts[profile] += 1
    return counts


def _count_trait_levels(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    trait_keys = [
        "self_efficacy",
        "question_tendency",
        "motivation",
        "extraversion",
        "conscientiousness",
        "neuroticism",
    ]
    counts = {key: {"low": 0, "medium": 0, "high": 0} for key in trait_keys}
    for result in results:
        traits = result.get("trait_estimates", {})
        for key in trait_keys:
            level = traits.get(key)
            if level in counts[key]:
                counts[key][level] += 1
    return counts


def _select_priority_students(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for result in results:
        traits = result.get("trait_estimates", {})
        score = 0
        if traits.get("self_efficacy") == "low":
            score += 3
        if traits.get("neuroticism") == "high":
            score += 3
        if traits.get("motivation") == "low":
            score += 2
        if traits.get("question_tendency") == "low":
            score += 1
        if result.get("profile_prediction") in {"A", "C"}:
            score += 1
        if score <= 0:
            continue
        scored.append(
            {
                "student_id": result.get("student_id"),
                "priority_score": score,
                "profile_prediction": result.get("profile_prediction"),
                "trait_estimates": traits,
                "teacher_summary": result.get("teacher_summary"),
                "recommended_teacher_attention": result.get(
                    "recommended_teacher_attention",
                    [],
                ),
            }
        )
    return sorted(scored, key=lambda row: row["priority_score"], reverse=True)[:5]


def _classroom_actions(
    *,
    profile_counts: dict[str, int],
    trait_level_counts: dict[str, dict[str, int]],
    priority_students: list[dict[str, Any]],
) -> list[str]:
    actions = []
    low_self = trait_level_counts["self_efficacy"]["low"]
    high_anxiety = trait_level_counts["neuroticism"]["high"]
    low_questions = trait_level_counts["question_tendency"]["low"]
    low_motivation = trait_level_counts["motivation"]["low"]

    if low_self + high_anxiety >= 2:
        actions.append("Start with a short confidence-building recap before asking for answers.")
    if low_questions >= 2:
        actions.append("Use teacher-initiated checks because several students may not ask questions.")
    if low_motivation >= 2:
        actions.append("Use one small problem at a time and keep the task goal visible.")
    if profile_counts.get("B", 0) + profile_counts.get("D", 0) >= 2:
        actions.append("Let confident or diligent students explain one step after individual thinking time.")
    if priority_students:
        actions.append("Check priority students individually before moving to a harder problem.")
    if not actions:
        actions.append("Continue the current explanation and verify understanding with one quick problem.")
    return actions


def _classroom_summary_text(
    *,
    student_count: int,
    profile_counts: dict[str, int],
    trait_level_counts: dict[str, dict[str, int]],
    priority_students: list[dict[str, Any]],
) -> str:
    priority_ids = [
        str(student["student_id"])
        for student in priority_students
        if student.get("student_id") is not None
    ]
    return (
        f"{student_count} students observed. "
        f"Profiles: A={profile_counts['A']}, B={profile_counts['B']}, "
        f"C={profile_counts['C']}, D={profile_counts['D']}. "
        f"Low self-efficacy={trait_level_counts['self_efficacy']['low']}, "
        f"high anxiety={trait_level_counts['neuroticism']['high']}, "
        f"low motivation={trait_level_counts['motivation']['low']}. "
        f"Priority students: {', '.join(priority_ids) if priority_ids else 'none'}."
    )


def _estimate_traits(features: dict[str, bool | int]) -> dict[str, str]:
    self_efficacy = "medium"
    if features["has_low_confidence"]:
        self_efficacy = "low"
    elif features["has_high_confidence"] and not features["shows_anxiety"]:
        self_efficacy = "high"

    question_tendency = "high" if features["asks_question"] else "low"
    motivation = "high" if features["shows_persistence"] else "medium"
    if features["short_answer"] and not features["shows_persistence"]:
        motivation = "low"

    extraversion = "high" if features["talkative_answer"] else "medium"
    if features["short_answer"]:
        extraversion = "low"

    conscientiousness = "high" if features["shows_steps"] else "medium"
    if features["short_answer"] and not features["shows_steps"]:
        conscientiousness = "low"

    neuroticism = "high" if features["shows_anxiety"] else "medium"
    if features["has_high_confidence"] and not features["shows_anxiety"]:
        neuroticism = "low"

    return {
        "self_efficacy": self_efficacy,
        "question_tendency": question_tendency,
        "motivation": motivation,
        "extraversion": extraversion,
        "conscientiousness": conscientiousness,
        "neuroticism": neuroticism,
    }


def _predict_profile(traits: dict[str, str], features: dict[str, bool | int]) -> str:
    scores = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }
    if traits["self_efficacy"] == "low":
        scores["A"] += 2
    if traits["question_tendency"] == "high":
        scores["A"] += 1
        scores["D"] += 1
    if traits["neuroticism"] == "high":
        scores["A"] += 2
    if traits["conscientiousness"] == "high":
        scores["B"] += 2
    if traits["motivation"] == "high":
        scores["B"] += 1
        scores["D"] += 1
    if traits["extraversion"] == "low":
        scores["C"] += 2
    if traits["motivation"] == "low":
        scores["C"] += 2
    if traits["self_efficacy"] == "high":
        scores["D"] += 2
    if traits["extraversion"] == "high":
        scores["D"] += 2
    if features["short_answer"]:
        scores["C"] += 1
    if features["shows_steps"] and features["shows_persistence"]:
        scores["B"] += 1

    return max(scores, key=lambda key: scores[key])


def _evidence(features: dict[str, bool | int]) -> list[str]:
    evidence = []
    if features["has_low_confidence"]:
        evidence.append("自信の低さを示す表現がある")
    if features["has_high_confidence"]:
        evidence.append("自信を示す表現がある")
    if features["asks_question"]:
        evidence.append("確認質問がある")
    if features["shows_anxiety"]:
        evidence.append("不安や迷いの表現がある")
    if features["shows_persistence"]:
        evidence.append("再挑戦や粘りの表現がある")
    if features["shows_steps"]:
        evidence.append("手順や途中式に触れている")
    if features["short_answer"]:
        evidence.append("返答が短い")
    if features["talkative_answer"]:
        evidence.append("返答量が多い")
    return evidence or ["発話特徴が弱く、標準的な反応に近い"]


def _confidence(features: dict[str, bool | int], profile: str) -> float:
    signal_count = sum(
        1
        for key, value in features.items()
        if key != "length" and bool(value)
    )
    base = min(0.95, 0.45 + signal_count * 0.08)
    if profile in {"A", "C"} and signal_count >= 3:
        base += 0.05
    return round(min(base, 0.98), 2)


def _teacher_summary(
    student_id: str | None,
    traits: dict[str, str],
    evidence: list[str],
) -> str:
    prefix = f"{student_id} は" if student_id else "この生徒は"
    return (
        f"{prefix}自己効力感={traits['self_efficacy']}、"
        f"質問傾向={traits['question_tendency']}、"
        f"不安傾向={traits['neuroticism']} と推定されます。"
        f"根拠: {'、'.join(evidence[:3])}。"
    )


def _recommended_teacher_attention(
    traits: dict[str, str],
    features: dict[str, bool | int],
) -> list[str]:
    attention = []
    if traits["self_efficacy"] == "low":
        attention.append("小さな成功体験を作り、自信を補強する")
    if traits["neuroticism"] == "high":
        attention.append("不安を下げる声かけを入れる")
    if traits["question_tendency"] == "low":
        attention.append("質問しやすい確認を教師側から入れる")
    if features["prefers_checking_sign"]:
        attention.append("移項時の符号変化を重点的に確認する")
    if traits["conscientiousness"] == "low":
        attention.append("途中式を1行だけ書かせる")
    if not attention:
        attention.append("現在の説明ペースを維持する")
    return attention
