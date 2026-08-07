from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import export_classroom_validity_for_codex, run_classroom_validity_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run classroom-level validity checks for multiple student-AI classes."
    )
    parser.add_argument(
        "--class-ids",
        default="class_3_basic,class_10_mixed,class_20_mixed,class_30_mixed",
        help="Comma-separated class IDs to evaluate.",
    )
    parser.add_argument("--classes-dir", default="data/classes")
    parser.add_argument("--students-dir", default="data/students")
    parser.add_argument("--cognitive-model", default="bkt_irt", choices=["legacy", "bkt_irt"])
    parser.add_argument("--output-dir", default="data/assessments")
    args = parser.parse_args()

    class_ids = [item.strip() for item in args.class_ids.split(",") if item.strip()]
    result = run_classroom_validity_evaluation(
        class_ids=class_ids,
        classes_dir=args.classes_dir,
        students_dir=args.students_dir,
        cognitive_model_type=args.cognitive_model,
    )
    output_path = export_classroom_validity_for_codex(
        result,
        output_path=Path(args.output_dir) / "classroom_validity_for_codex.txt",
    )
    print(
        json.dumps(
            {
                "cognitive_model": result["cognitive_model"],
                "class_ids": result["class_ids"],
                "summary": result["summary"],
                "output_file": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
