from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AnswerLogger:
    def __init__(
        self,
        logs_dir: str | Path = "data/logs",
        jsonl_name: str = "machine_readable.jsonl",
        markdown_name: str = "human_readable.md",
    ) -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.logs_dir / jsonl_name
        self.markdown_path = self.logs_dir / markdown_name

    def log_interaction(
        self,
        *,
        student_id: str,
        problem: str,
        answer: str,
        student_state_snapshot: dict[str, Any],
        model_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "student_id": student_id,
            "problem": problem,
            "answer": answer,
            "student_state_snapshot": student_state_snapshot,
            "model_id": model_id,
            "metadata": metadata or {},
        }
        self._append_jsonl(record)
        self._append_markdown(record)
        return record

    def _append_jsonl(self, record: dict[str, Any]) -> None:
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _append_markdown(self, record: dict[str, Any]) -> None:
        lines = [
            f"## {record['timestamp']} - {record['student_id']}",
            "",
            f"- Model: `{record['model_id']}`",
            f"- Problem: {record['problem']}",
            "",
            "### Answer",
            "",
            record["answer"],
            "",
        ]
        with self.markdown_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines))
