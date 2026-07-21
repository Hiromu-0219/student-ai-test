from __future__ import annotations

import json
from pathlib import Path


MARKER = "<!-- student-ai-expanded-evaluation -->"
NOTEBOOK_PATH = Path("notebooks/student_ai_colab.ipynb")


def markdown_cell(source: str) -> dict:
    if not source.endswith("\n"):
        source += "\n"
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code_cell(source: str) -> dict:
    if not source.endswith("\n"):
        source += "\n"
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    if any(MARKER in cell_source(cell) for cell in notebook["cells"]):
        print("student AI evaluation cells already exist")
        return

    notebook["cells"].extend(
        [
            markdown_cell(
                f"""{MARKER}
## 19. Expanded student AI evaluation

生徒AI単体の制御妥当性をまとめて確認します。

このセルでは、次を一度に出します。

- 理解度と正答率の学習曲線
- 誤概念あり/なしの比較
- スキル別の弱点比較
- 個人特徴を変えた発話サンプル

結果は `data/assessments/student_ai_evaluation_summary.txt` に保存されます。
"""
            ),
            code_cell(
                """from pprint import pprint

from src.experiment import export_student_ai_evaluation, run_student_ai_evaluation

student_ai_evaluation = run_student_ai_evaluation(
    student_id=STUDENT_ID,
    test_id="linear_equation_20q_001",
    understanding_levels=list(range(0, 101, 10)),
    use_mock_model=USE_MOCK_MODEL,
)

summary_path = export_student_ai_evaluation(student_ai_evaluation)

print("summary_path:", summary_path)
print("\\nsummary:")
pprint(student_ai_evaluation["summary"])

print("\\nlearning_curve:")
for row in student_ai_evaluation["learning_curve"]:
    print(row)

print("\\nutterance_samples:")
for sample in student_ai_evaluation["utterance_samples"]:
    print(f"- {sample['profile_id']}: {sample['utterance']}")
"""
            ),
        ]
    )
    NOTEBOOK_PATH.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"updated {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
