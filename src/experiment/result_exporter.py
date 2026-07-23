from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def export_teaching_strategy_summary(
    result: dict[str, Any],
    *,
    output_path: str | Path = "data/assessments/teaching_strategy_result_summary.txt",
) -> Path:
    """Export a compact text summary for sharing Colab results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Teaching Strategy Experiment Result Summary",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Experiment Summary",
        json.dumps(result.get("summary", {}), ensure_ascii=False, indent=2),
        "",
        "## Lecture Design",
        json.dumps(
            {
                "objective": result.get("lecture_design", {}).get("objective"),
                "class_diagnosis": result.get("lecture_design", {}).get("class_diagnosis"),
                "optimization_targets": result.get("lecture_design", {}).get("optimization_targets"),
                "whole_class_policy": result.get("lecture_design", {})
                .get("recommended_lecture", {})
                .get("whole_class_policy"),
                "observable_input_policy": result.get("lecture_design", {}).get("observable_input_policy"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "## Lesson Goal",
        json.dumps(result.get("lesson_plan", {}).get("lesson_goal", {}), ensure_ascii=False, indent=2),
        "",
        "## Initial Class Profile",
        json.dumps(result.get("lesson_plan", {}).get("class_profile", {}), ensure_ascii=False, indent=2),
        "",
        "## Final Class Profile",
        json.dumps(result.get("session_result", {}).get("final_class_profile", {}), ensure_ascii=False, indent=2),
        "",
        "## Phase Summary",
    ]
    for phase in result.get("phase_summary", []):
        lines.append(json.dumps(phase, ensure_ascii=False))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
