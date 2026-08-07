# Notebook Guide

Colabで実行する実験Notebookの使い分けです。LLMロードは時間がかかるため、まずはmock modelやルールベースのセルで表や評価指標を確認し、必要なときだけLLMセルを実行します。

## 推奨順

| 順番 | Notebook | 目的 |
| --- | --- | --- |
| 1 | `communication_ai_rq1_experiment.ipynb` | 主研究用。伝達AIが観察ログからTeacher Beliefを推定できるかを評価する |
| 2 | `simulation_timeline_experiment.ipynb` | 実行環境用。LLMを任意で入れながら教育シミュレーションを時間経過で確認する |
| 3 | `student_ai_presentation_experiment.ipynb` | 生徒AI設計の発表用。認知モデル、テスト結果、性格別発話、複数生徒分布をまとめて見る |
| 4 | `student_ai_colab.ipynb` | 生徒AI単体の詳細確認。理解度、誤概念、難易度、スキル弱点、発話サンプルを見る |
| 5 | `personality_experiment.ipynb` | 個人特徴が発話に反映され、伝達AIが分類できるかを見る |
| 6 | `teaching_strategy_experiment.ipynb` | 複数生徒クラスを観察し、伝達AI、講義設計AI、教師発話AIの流れを見る |
| 7 | `paper_core_experiment.ipynb` | 論文に使う最小実験と出力結果をまとめて確認する |

## 最初に実行するNotebook

伝達AIを主研究として確認する場合は、まず `communication_ai_rq1_experiment.ipynb` から始めます。

このNotebookで確認するもの:

- Ground Truth StateとObservable Eventの分離
- Observable EventだけからTeacher Belief Stateを推定する流れ
- `stats_baseline`, `rule_based_communication_ai`, `enhanced_communication_ai` の比較
- 観察情報アブレーションによる性能変化
- スキル習熟度、全体理解度、誤概念、個人特徴、確信度の評価
- 失敗例と追加観察候補
- Codex/ChatGPT共有用txtの出力

生徒AI設計の進捗報告や発表では、`student_ai_presentation_experiment.ipynb` を使います。

発表用Notebookで確認するもの:

- 認知モデルの式
- 100問テストでの理解度とテスト結果の関係
- 問題難易度、誤概念、スキル弱点の影響
- 性格別の発話サンプル
- 実際のLLMによる性格別発話差の任意確認
- 複数生徒AIにしたときのクラス分布
- 30人分のパラメータ設計と予測正答率分布
- 従来モデルとBKT/IRT寄りモデルの補助比較

## スライド用の材料

スライドに貼る材料を作る場合は、`student_ai_colab.ipynb` の後半にある次のセルを使います。

| セル | 内容 |
| --- | --- |
| `21. Slide-ready cognitive model equations` | 正答確率を決める式と記号説明 |
| `22. Multiple student AI visualization` | 複数生徒の理解度分布、予測正答確率、スキルヒートマップ |
| `23. What changes from one student to many students?` | 1人の生徒AIと複数生徒AIの違い |

## LLMセルの扱い

LLM発話の自然性を確認するセルは、ロード時間が長いため標準では実行しない構成にしています。必要なときだけ `use_mock_model=False` や実行フラグを有効にしてください。

ColabでLLMを使う場合:

```text
ランタイム > ランタイムのタイプを変更 > GPU
```

4bit量子化を使う場合は `bitsandbytes` が必要です。CPUランタイムでは4bitロードが失敗することがあります。

## 結果共有

Codex/ChatGPTに結果を渡すときは、Notebookの出力を大量に貼るのではなく、共有用txtを作成して添付します。

```text
data/assessments/rq1_communication_ai_for_codex.txt
data/assessments/simulation_timeline_for_codex.txt
data/assessments/student_ai_evaluation_for_codex.txt
data/assessments/cognitive_model_comparison_for_codex.txt
data/assessments/teaching_strategy_result_summary.txt
```

## Notebookを更新した場合

ColabでGit更新セルを実行しても、すでに開いているNotebook画面のセル内容は自動更新されないことがあります。Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。
