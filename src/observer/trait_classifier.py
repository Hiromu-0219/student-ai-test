from __future__ import annotations

from dataclasses import dataclass
from typing import Any


LEVELS = ("low", "medium", "high")


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
