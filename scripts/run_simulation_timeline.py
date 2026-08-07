from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.experiment import export_simulation_timeline_results, run_simulation_timeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a time-series education simulation.")
    parser.add_argument("--class-id", default="class_10_mixed")
    parser.add_argument("--class-size", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--total-minutes", type=int, default=30)
    parser.add_argument("--use-llm-student", action="store_true")
    parser.add_argument("--use-llm-communication", action="store_true")
    parser.add_argument("--model-id", default="Qwen/Qwen3-4B")
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--cognitive-model", choices=["legacy", "bkt_irt"], default="bkt_irt")
    parser.add_argument("--update-student-knowledge", action="store_true")
    parser.add_argument("--output-dir", default="data/assessments")
    args = parser.parse_args()

    result = run_simulation_timeline(
        class_id=args.class_id,
        class_size=args.class_size,
        cycles=args.cycles,
        total_minutes=args.total_minutes,
        use_llm_student=args.use_llm_student,
        use_llm_communication=args.use_llm_communication,
        model_id=args.model_id,
        load_in_4bit=not args.no_4bit,
        cognitive_model_type=args.cognitive_model,
        update_student_knowledge=args.update_student_knowledge,
    )
    outputs = export_simulation_timeline_results(result, output_dir=args.output_dir)
    print(json.dumps({
        "experiment": result["experiment"],
        "conditions": result["conditions"],
        "research_metrics": result["research_metrics"],
        "issue_count": len(result["issue_candidates"]),
        "outputs": outputs,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
