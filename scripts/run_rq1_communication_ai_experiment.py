from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import export_rq1_communication_ai_results, run_rq1_communication_ai_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RQ1 communication-AI evaluation.")
    parser.add_argument("--class-id", default="class_10_mixed")
    parser.add_argument("--class-size", type=int, default=None)
    parser.add_argument("--question-count", type=int, default=8)
    parser.add_argument("--classes-dir", default="data/classes")
    parser.add_argument("--students-dir", default="data/students")
    parser.add_argument("--test-path", default="data/tests/linear_equation_20q_001.json")
    parser.add_argument("--cognitive-model", default="bkt_irt", choices=["legacy", "bkt_irt"])
    parser.add_argument("--seed", type=int, default=20260807)
    parser.add_argument("--output-dir", default="data/assessments")
    args = parser.parse_args()

    result = run_rq1_communication_ai_experiment(
        class_id=args.class_id,
        class_size=args.class_size,
        question_count=args.question_count,
        classes_dir=args.classes_dir,
        students_dir=args.students_dir,
        test_path=args.test_path,
        cognitive_model_type=args.cognitive_model,
        seed=args.seed,
    )
    outputs = export_rq1_communication_ai_results(result, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "experiment": result["experiment"],
                "conditions": result["conditions"],
                "summary": result["summary"],
                "leakage_check": result["leakage_check"],
                "outputs": outputs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
