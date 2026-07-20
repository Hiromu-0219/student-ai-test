from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from typing import Any

from src.config import (
    DEFAULT_LOGS_DIR,
    DEFAULT_MODEL_ID,
    DEFAULT_STUDENTS_DIR,
    GenerationConfig,
    ModelLoadConfig,
)
from src.learning_updater import LearningUpdater
from src.logger import AnswerLogger
from src.model_loader import LocalLLM
from src.student_agent import StudentAgent
from src.state_manager import StateManager


class RuleBasedMockLLM:
    model_id = "rule-based-mock"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        target_answer = _extract_target_answer(user_prompt)
        if target_answer:
            if "学力テスト" in system_prompt:
                return f"答え: {target_answer}"
            return f"考えてみると、{target_answer} だと思います。答え: {target_answer}"
        problem = _extract_problem(user_prompt)
        answer = _solve_simple_linear_equation(problem)
        if answer is None:
            return "まだ一次方程式として整理できていません。答え: わかりません"
        return _style_mock_answer(user_prompt, answer)


class StudentAISimulator:
    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        load_in_4bit: bool = True,
        students_dir: str = DEFAULT_STUDENTS_DIR,
        logs_dir: str = DEFAULT_LOGS_DIR,
        use_mock_model: bool = False,
        generation_config: GenerationConfig | None = None,
        model_load_config: ModelLoadConfig | None = None,
        speech_generator: Any | None = None,
    ) -> None:
        self.state_manager = StateManager(students_dir)
        self.logger = AnswerLogger(logs_dir)
        if speech_generator is not None:
            self.llm = speech_generator
        elif use_mock_model:
            self.llm = RuleBasedMockLLM()
        else:
            self.llm = LocalLLM(
                model_id=model_id,
                load_in_4bit=load_in_4bit,
                generation_config=generation_config,
                model_load_config=model_load_config,
            )
        self.agent = StudentAgent(self.llm)
        self.learning_updater = LearningUpdater()

    def respond(
        self,
        student_id: str,
        teacher_message: str,
        *,
        update_knowledge: bool = True,
        assessment_directive: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.state_manager.load_student(student_id)
        answer = self.agent.answer(state, teacher_message, assessment_directive)
        updated_state = state
        learning_event = {
            "knowledge_delta": 0,
            "updated_score": state.get("knowledge_state", {})
            .get("linear_equation", {})
            .get("score"),
            "updated_level": state.get("knowledge_state", {})
            .get("linear_equation", {})
            .get("level"),
            "touched_skills": [],
            "update_enabled": False,
        }
        if update_knowledge:
            updated_state, learning_event = self.learning_updater.update_after_interaction(
                state,
                teacher_message=teacher_message,
                student_answer=answer,
            )
            learning_event["update_enabled"] = True
        record = self.logger.log_interaction(
            student_id=student_id,
            problem=teacher_message,
            answer=answer,
            student_state_snapshot=state,
            model_id=self.agent.model_id,
            metadata={
                "domain": "linear_equation",
                "interaction_type": "lesson_dialogue",
                "learning_event": learning_event,
                "assessment_directive": assessment_directive,
            },
        )
        if update_knowledge:
            updated_state["learning_history"].append(
                {
                    "teacher_message": teacher_message,
                    "answer": answer,
                    "logged_at": record["timestamp"],
                    "domain": "linear_equation",
                    "interaction_type": "lesson_dialogue",
                    "learning_event": learning_event,
                }
            )
            self.state_manager.save_student(updated_state)
        return record

    def answer(self, student_id: str, problem: str) -> dict[str, Any]:
        return self.respond(student_id, problem)

    def apply_learning_intervention(
        self,
        student_id: str,
        *,
        skill_deltas: dict[str, int],
        resolve_misconceptions: bool = True,
    ) -> dict[str, Any]:
        state = self.state_manager.load_student(student_id)
        updated_state, event = self.learning_updater.apply_controlled_learning(
            state,
            skill_deltas=skill_deltas,
            resolve_misconceptions=resolve_misconceptions,
        )
        event["logged_at"] = datetime.now(timezone.utc).isoformat()
        event["interaction_type"] = "controlled_learning_intervention"
        updated_state["learning_history"].append(event)
        self.state_manager.save_student(updated_state)
        return event


def _extract_problem(prompt: str) -> str:
    marker = "教師の発話:"
    if marker in prompt:
        return prompt.split(marker, 1)[1].split("生徒AIとして", 1)[0].strip()
    marker = "問題:"
    if marker in prompt:
        return prompt.split(marker, 1)[1].split("生徒AIとして", 1)[0].strip()
    return prompt


def _extract_target_answer(prompt: str) -> str | None:
    match = re.search(r"target_answer:\s*(x\s*=\s*[+-]?\d+(?:/\d+)?)", prompt)
    if match:
        return match.group(1)
    match = re.search(r"'target_answer': '([^']+)'", prompt)
    if match:
        return match.group(1)
    match = re.search(r'"target_answer": "([^"]+)"', prompt)
    if match:
        return match.group(1)
    return None


def _style_mock_answer(prompt: str, answer: str) -> str:
    if "返答は短めにする" in prompt:
        base = f"x = {answer}。"
    elif "途中式や手順を丁寧に出す" in prompt:
        base = f"まず定数を移して、それから係数で割ります。x = {answer} です。"
    elif "途中式を省略しがちにする" in prompt:
        base = f"たぶん x = {answer} です。"
    else:
        base = f"両辺を整理して、x は {answer} だと思います。"

    if "自信なさげに、断定を避けて答える" in prompt:
        base = "自信はないけど、" + base
    elif "自信を持って、はっきり答える" in prompt:
        base = "これは分かります。" + base

    if "不安や確認したい気持ちを少し出す" in prompt:
        base += " 符号が合っているか少し不安です。"
    if "わからない点があれば具体的に質問する" in prompt:
        base += " 移項の符号はこの考え方で合っていますか。"
    if "間違えてももう一度考えようとする" in prompt:
        base += " 間違っていたらもう一度考えます。"
    if "教師への反応は少しそっけなくする" in prompt:
        base = base.replace("これは分かります。", "")

    return f"{base} 答え: x = {answer}"


def _solve_simple_linear_equation(text: str) -> str | None:
    normalized = (
        text.replace(" ", "")
        .replace("\u3000", "")
        .replace("を解いてください。", "")
        .replace("を解いてください", "")
        .replace("を解いてみましょう。", "")
    )
    match = re.search(r"([+-]?\d*)x([+-]\d+)?=([+-]?\d+)", normalized)
    if not match:
        return None

    coef_raw, const_raw, rhs_raw = match.groups()
    if coef_raw in ("", "+"):
        coef = 1
    elif coef_raw == "-":
        coef = -1
    else:
        coef = int(coef_raw)

    const = int(const_raw or 0)
    rhs = int(rhs_raw)
    if coef == 0:
        return None

    value = (rhs - const) / coef
    return str(int(value)) if value.is_integer() else str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the student AI simulator.")
    parser.add_argument("--student-id", default="S001")
    parser.add_argument("--problem", required=True)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    args = parser.parse_args()

    sim = StudentAISimulator(
        model_id=args.model_id,
        load_in_4bit=not args.no_4bit,
        use_mock_model=args.mock,
        generation_config=GenerationConfig(
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
        ),
    )
    result = sim.answer(args.student_id, args.problem)
    print(result["answer"])


if __name__ == "__main__":
    main()
