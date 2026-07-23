# Notebook Guide

Colabで実行する実験Notebookの使い分けです。LLMロードは時間がかかるため、まずは `use_mock_model=True` のセルで表や評価指標を確認し、必要なときだけLLMセルを実行します。

## 推奨順

| 順番 | Notebook | 目的 |
| --- | --- | --- |
| 1 | `student_ai_colab.ipynb` | 生徒AI単体の妥当性確認。理解度、誤概念、難易度、スキル弱点、発話サンプルを見る |
| 2 | `personality_experiment.ipynb` | 個人特徴が発話に反映され、伝達AIが分類できるかを見る |
| 3 | `teaching_strategy_experiment.ipynb` | 複数生徒クラスを観察し、伝達AI、講義設計AI、教師発話AIの流れを見る |
| 4 | `paper_core_experiment.ipynb` | 論文に使う最小実験と出力結果をまとめて確認する |

## 最初に実行するNotebook

生徒AIの設計を確認したい場合は `student_ai_colab.ipynb` から始めます。

主に確認するもの:

- 理解度と正答率の関係
- 問題難易度別の正答率
- 誤概念あり/なしの差
- 弱点スキルごとの差
- 個人特徴による発話の違い
- BKT/IRT寄りモデルと従来モデルの比較

## LLMセルの扱い

LLM発話の自然性を確認するセルは、ロード時間が長いため標準では実行しない構成にしています。必要なときだけ `use_mock_model=False` にして実行してください。

ColabでLLMを使う場合:

```text
ランタイム > ランタイムのタイプを変更 > GPU
```

4bit量子化を使う場合は `bitsandbytes` が必要です。CPUランタイムでは4bitロードが失敗することがあります。

## 結果共有

Codex/ChatGPTに結果を渡すときは、Notebookの出力を大量に貼るのではなく、共有用txtを作成して添付します。

```text
data/assessments/student_ai_evaluation_for_codex.txt
data/assessments/cognitive_model_comparison_for_codex.txt
data/assessments/teaching_strategy_result_summary.txt
```

## Notebookを更新した場合

ColabでGit更新セルを実行しても、すでに開いているNotebook画面のセル内容は自動更新されないことがあります。Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。
