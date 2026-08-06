from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import (
    compare_cognitive_models,
    export_cognitive_model_comparison_for_codex,
    export_student_ai_evaluation,
    export_student_ai_evaluation_for_codex,
    run_student_ai_evaluation,
)


def _levels(raw: str) -> list[int]:
    values = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    if not values:
        raise argparse.ArgumentTypeError("at least one understanding level is required")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run internal-validity checks for the student AI cognitive model "
            "and export Codex/ChatGPT-friendly txt files."
        )
    )
    parser.add_argument("--student-id", default="S002")
    parser.add_argument("--test-id", default="linear_equation_20q_001")
    parser.add_argument("--cognitive-model", default="bkt_irt", choices=["legacy", "bkt_irt"])
    parser.add_argument(
        "--understanding-levels",
        type=_levels,
        default=list(range(0, 101, 10)),
        help="Comma-separated values, e.g. 0,10,20,...,100",
    )
    parser.add_argument("--students-dir", default="data/students")
    parser.add_argument("--tests-dir", default="data/tests")
    parser.add_argument("--logs-dir", default="data/logs")
    parser.add_argument("--output-dir", default="data/assessments")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use the configured local LLM for personality utterance samples. Default uses mock generation.",
    )
    parser.add_argument(
        "--skip-model-comparison",
        action="store_true",
        help="Only run the selected cognitive model, not legacy vs BKT/IRT comparison.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_student_ai_evaluation(
        student_id=args.student_id,
        test_id=args.test_id,
        understanding_levels=args.understanding_levels,
        students_dir=args.students_dir,
        tests_dir=args.tests_dir,
        logs_dir=args.logs_dir,
        use_mock_model=not args.use_llm,
        cognitive_model_type=args.cognitive_model,
    )
    summary_path = export_student_ai_evaluation(
        result,
        output_path=output_dir / "student_ai_internal_validity_summary.txt",
    )
    codex_path = export_student_ai_evaluation_for_codex(
        result,
        output_path=output_dir / "student_ai_internal_validity_for_codex.txt",
    )

    comparison_path = None
    comparison_summary = None
    if not args.skip_model_comparison:
        comparison = compare_cognitive_models(
            student_id=args.student_id,
            test_id=args.test_id,
            understanding_levels=args.understanding_levels,
            students_dir=args.students_dir,
            tests_dir=args.tests_dir,
            logs_dir=args.logs_dir,
            use_mock_model=not args.use_llm,
        )
        comparison_path = export_cognitive_model_comparison_for_codex(
            comparison,
            output_path=output_dir / "cognitive_model_comparison_for_codex.txt",
        )
        comparison_summary = comparison.get("summary")

    run_summary = {
        "student_id": args.student_id,
        "test_id": args.test_id,
        "cognitive_model": args.cognitive_model,
        "use_llm": args.use_llm,
        "internal_validity_summary": result.get("summary"),
        "model_comparison_summary": comparison_summary,
        "output_files": {
            "summary": str(summary_path),
            "codex": str(codex_path),
            "model_comparison": str(comparison_path) if comparison_path else None,
        },
    }
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
