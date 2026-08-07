from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import (
    export_lesson_design_validity_for_codex,
    run_lesson_design_validity_evaluation,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run lesson-design AI validity checks across classroom scenarios."
    )
    parser.add_argument("--curriculum-path", default="data/curriculum/linear_equation.json")
    parser.add_argument("--total-minutes", type=int, default=30)
    parser.add_argument("--output-dir", default="data/assessments")
    args = parser.parse_args()

    result = run_lesson_design_validity_evaluation(
        curriculum_path=args.curriculum_path,
        total_minutes=args.total_minutes,
    )
    output_path = export_lesson_design_validity_for_codex(
        result,
        output_path=Path(args.output_dir) / "lesson_design_validity_for_codex.txt",
    )
    print(
        json.dumps(
            {
                "experiment": result["experiment"],
                "summary": result["summary"],
                "output_file": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
