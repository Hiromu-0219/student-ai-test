from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import (
    export_communication_validity_for_codex,
    run_communication_validity_evaluation,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run communication-AI validity checks using observable classroom data only."
    )
    parser.add_argument("--class-id", default="class_30_mixed")
    parser.add_argument("--classes-dir", default="data/classes")
    parser.add_argument("--students-dir", default="data/students")
    parser.add_argument("--cognitive-model", default="bkt_irt", choices=["legacy", "bkt_irt"])
    parser.add_argument("--output-dir", default="data/assessments")
    args = parser.parse_args()

    result = run_communication_validity_evaluation(
        class_id=args.class_id,
        classes_dir=args.classes_dir,
        students_dir=args.students_dir,
        cognitive_model_type=args.cognitive_model,
    )
    output_path = export_communication_validity_for_codex(
        result,
        output_path=Path(args.output_dir) / "communication_validity_for_codex.txt",
    )
    print(
        json.dumps(
            {
                "class_id": result["class_id"],
                "student_count": result["student_count"],
                "cognitive_model": result["cognitive_model"],
                "summary": result["summary"],
                "output_file": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
