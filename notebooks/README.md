# Notebook Guide

研究の流れが分かるように、既存Notebookを次の役割で使います。

| 順番 | Notebook | 目的 |
| --- | --- | --- |
| 00 | `paper_core_experiment.ipynb` | 論文用の最小実験、使用ソース、確認観点を整理する |
| 01 | `student_ai_colab.ipynb` | 生徒AI単体の状態制御、学習曲線、誤概念、発話サンプルを確認する |
| 02 | `personality_experiment.ipynb` | 個人特徴が発話に反映され、伝達AIが分類できるか確認する |
| 03 | `teaching_strategy_experiment.ipynb` | 複数生徒クラス、伝達AI要約、教師AIの授業方針生成を確認する |

## まず見るNotebook

人間学習者の限定的代理としての妥当性を確認したい場合は、まず `student_ai_colab.ipynb` の生徒AI評価セルを実行します。

主な呼び出し:

```python
from src.experiment import (
    export_student_ai_evaluation,
    export_student_ai_evaluation_for_codex,
    run_student_ai_evaluation,
)

result = run_student_ai_evaluation(
    student_id="S002",
    test_id="linear_equation_20q_001",
    understanding_levels=list(range(0, 101, 10)),
    use_mock_model=True,
)

export_student_ai_evaluation(result)
export_student_ai_evaluation_for_codex(result)
```

この実験では次を確認できます。

- Learning Curve
- Misconception Comparison
- Skill Breakdown
- Utterance Samples
- Human Replacement Validity

Codex/ChatGPTに共有する場合は、次のファイルを添付してください。

```text
data/assessments/student_ai_evaluation_for_codex.txt
```

## LLMを使う場合

`use_mock_model=False` にするとLLM発話を使います。ColabではGPUランタイムを選び、必要に応じてHugging Faceへログインしてください。

LLMロードは時間がかかるため、研究設計や表の確認はまず `use_mock_model=True` で行い、発話自然性の確認だけLLM条件で実行するのがおすすめです。

## Notebookを更新した場合

ColabでGit更新セルを実行しても、すでに開いているNotebook画面のセル内容は自動更新されないことがあります。

Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。
