from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AssessmentLogger:
    def __init__(
        self,
        assessments_dir: str | Path = "data/assessments",
        jsonl_name: str = "machine_readable.jsonl",
        markdown_name: str = "human_readable.md",
    ) -> None:
        self.assessments_dir = Path(assessments_dir)
        self.assessments_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.assessments_dir / jsonl_name
        self.markdown_path = self.assessments_dir / markdown_name

    def log_assessment(self, result: dict[str, Any]) -> dict[str, Any]:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._append_markdown(record)
        return record

    def _append_markdown(self, record: dict[str, Any]) -> None:
        lines = [
            f"## {record['timestamp']} - {record['student_id']} - {record['test_id']}",
            "",
            f"- Title: {record['title']}",
            f"- Score: {record['score_percentage']}%",
            f"- Correct: {record['correct_count']} / {record['total_count']}",
            "",
            "### Skill Scores",
            "",
        ]
        for skill, score in record["skill_scores"].items():
            lines.append(f"- `{skill}`: {score}%")
        lines.extend(["", "### Questions", ""])
        for item in record["question_results"]:
            mark = "correct" if item["grading"]["is_correct"] else "incorrect"
            lines.extend(
                [
                    f"- {item['question_id']} ({mark})",
                    f"  - Problem: {item['problem']}",
                    f"  - Student: {item['student_answer']}",
                    f"  - Expected: {item['expected_answer']}",
                ]
            )
        lines.append("")
        with self.markdown_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines))
