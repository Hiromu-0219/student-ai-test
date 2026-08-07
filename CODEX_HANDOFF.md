# Codex Handoff

最終更新: 2026-08-07 15:51:27 JST

このファイルは、別PCや別Codexセッションへ研究開発を引き継ぐためのメモです。新しいCodexには、最初にこのファイルを読ませてください。

## リポジトリ

- Repository: https://github.com/Hiromu-0219/student-ai-test.git
- Main branch: `main`
- 作業ディレクトリ例: `C:\Users\hiro\Desktop\ai-sim\student-ai`
- Colab実行前提。ローカルPCでは主に編集・pytest・pushを行う。

## 研究目的

目的は、個別の生徒AIを教育することではなく、複数の生徒AIからなるクラス全体を観察し、教師AIが授業構成・介入方針を変えられるかを検証すること。

現在の設計では、生徒AIの正誤や理解度は認知モデルで制御し、LLMは発話生成器として使う。これにより、教育シミュレーション内で「正答率・誤概念・個人特徴」を制御しつつ、授業中に観察できる発話として外に出す。

## 現在の中心設計

### 生徒AI

- 内部状態は `data/students/Sxxx.json` で管理する。
- 主な状態:
  - `knowledge_state.linear_equation.score`
  - `can_solve_ax_plus_b_equals_c`
  - `can_transpose_terms`
  - `can_divide_by_coefficient`
  - `can_handle_negative_numbers`
  - `can_handle_fractions`
  - `misconceptions`
  - `self_efficacy`
  - `question_tendency`
  - `motivation`
  - `big_five`
- 正誤は `src/cognitive_model.py` の BKT/IRT 寄りモデルで制御する。
- LLMは、認知モデルが決めた `target_answer` に従って、生徒らしい発話を生成する。

### 認知モデル

中心ファイル: `src/cognitive_model.py`

現在は `BKTIRTCognitiveModel` を使用する。これは実データで推定した本格BKT/IRTではなく、教育シミュレーション用の制御可能な近似モデル。

ざっくりした役割:

- スキル理解度と全体理解度から能力値を作る。
- 問題難易度を加味する。
- guess/slip を入れて、理解度が低くてもたまに正解し、高くてもまれに間違うようにする。
- 誤概念がある場合は正答確率を下げる。
- 最終的に `target_correct` と `target_answer` を決める。

### LLMの役割

LLMは「正誤判定者」ではなく「発話生成器」。

重要:

- 認知モデルが `target_answer` を決める。
- LLMはその答えを含む自然な生徒発話を作る。
- `lesson_probe` では、LLMが勝手に正答を書いても、最後の `答え: x = ...` は認知モデルの `target_answer` に強制される。
- この修正は `src/student_agent.py` の `_force_controlled_answer_label` にある。

## 教育シミュレーションの流れ

1. 教師が代表問題を出す。
2. 各生徒AIの内部状態から認知モデルが正誤・回答を決める。
3. LLMまたはmockが、生徒ごとの性格に合わせて発話を生成する。
4. 観察可能な情報だけを `observable_event` にする。
5. 伝達AIが発話・正誤・反応から生徒特徴を推定する。
6. 教師beliefを更新する。
7. 講義設計AIがクラス全体の状況から授業構成を決める。
8. 介入計画AIが全体方針と個別支援を決める。
9. 教師発話AIが全体向け・個別向け発話を作る。

## 重要Notebook

### `notebooks/teaching_strategy_experiment.ipynb`

現在の最重要Notebook。教育シミュレーションの流れを確認する。

使う設定:

```python
EXPERIMENT_MODE = "llm_student_observer"
```

モード:

- `mock_fast`: LLMなし。高速な構造確認用。
- `llm_student_only`: 生徒発話だけLLM。
- `llm_student_observer`: 生徒発話と伝達AIをLLM。現在の主実験候補。
- `llm_full`: 生徒発話、伝達AI、教師発話をLLM。重いので後回し。

Colabでは上から順に実行する。Git更新セル、setupセル、preflightセルを先に通す。

### `notebooks/student_ai_presentation_experiment.ipynb`

生徒AIそのものの設計説明・発表用Notebook。認知モデル、理解度と正答率、性格別発話などを見せる用途。

### `notebooks/student_ai_colab.ipynb`

初期からある生徒AI検証Notebook。現在は補助的位置づけ。

### `notebooks/paper_core_experiment.ipynb`

論文用のコア実験整理用。必要なら今後再整理。

## 直近の重要コミット

- `800ffe4 Enforce controlled answers in LLM lesson probes`
  - LLMが勝手に正答へ戻しても、認知モデルの `target_answer` を最終回答に強制。
  - LLMロード時間を代表問題の応答時間に混ぜないよう、Notebook側で事前ロード。
- `f06dd20 Add LLM lesson probe mode`
  - `EXPERIMENT_MODE` を追加。
  - `lesson_probe` 用プロンプトを追加。
  - LLM生徒発話・LLM伝達AIを切り替え可能にした。
- `8fdc56c Use cognitive model for teaching strategy probe`
  - 授業中の代表問題も認知モデルで正誤制御するよう変更。
- `960aa91 Add teaching simulation preflight checks`
  - Colabで古いコードを読んでいないか事前確認するセルを追加。

## Colabでの実行手順

1. ColabをGPUにする。
2. Notebook上部のGit更新セルを実行する。
3. ランタイム再起動が必要なら再起動する。
4. setupセルを実行する。
5. preflightセルを実行する。
6. 設定セルで以下を確認する。

```text
experiment_mode: llm_student_observer
use_llm_student_utterances: True
use_llm_communication_ai: True
use_llm_teacher_utterances: False
```

7. LLM準備セルで以下が出るか確認する。

```text
loading shared LLM: Qwen/Qwen2.5-1.5B-Instruct
shared LLM loaded
student_generator: Qwen/Qwen2.5-1.5B-Instruct
```

8. 最後に `data/assessments/teaching_strategy_result_summary.txt` が生成される。
9. そのtxtをCodexに渡して結果確認する。

## 結果確認で見るべき点

`teaching_strategy_result_summary.txt` では次を見る。

- Settings:
  - `experiment_mode`
  - `llm_model_id`
  - `use_llm_student_utterances`
  - `use_llm_communication_ai`
- Classroom Response Table:
  - `utterance`
  - `controlled_answer`
  - `is_correct`
  - `correct_probability`
  - `skill_score`
  - `response_time_sec`
- Communication AI Summary:
  - `profile_counts`
  - `trait_level_counts`
  - `priority_students`
- Lecture Design:
  - `class_diagnosis`
  - `optimization_targets`
  - `recommended_lecture`
- Intervention Plan:
  - `whole_class_plan`
  - `individual_supports`

特に重要なのは、`utterance` の最後の `答え: x = ...` と `controlled_answer` が一致していること。

## 現在の注意点

- Colab側で古いNotebookを開いたままだと、最新コードが反映されないことがある。Git更新後にランタイム再起動する。
- LLMロードは長い。Qwen/Qwen2.5-1.5Bでも数分かかる場合がある。
- Qwen3-4BやGemma 3 4Bはさらに重い。まずは `Qwen/Qwen2.5-1.5B-Instruct` で流れ確認する。
- `RUN_FULL_LESSON_SESSION` はLLMモードでは初期値False。フル授業までLLMで回すと非常に時間がかかる。
- 伝達AIがLLMの場合、推定理由に雑な文が出ることがある。ここは今後改善対象。
- 現時点では実人間データとの外的妥当性までは主張しない。内部妥当性、制御可能性、一貫性の検証が中心。

## ローカルPCでの確認

ローカルはLLMを読まず、テスト中心。

```powershell
cd C:\Users\hiro\Desktop\ai-sim\student-ai
py -m pytest
git status
```

現在のテスト期待値:

```text
77 passed
```

## Git運用

変更後は基本的にmainへpushする。

```powershell
git status
git add <changed files>
git commit -m "message"
git push origin main
```

ユーザーは「確認なしでpushしてよい」と言っているので、Codexは編集後にテストを通してpushまで行う。

## 次にやるとよさそうなこと

1. Colabで `800ffe4` 以降をpullし、LLM実験を再実行する。
2. `teaching_strategy_result_summary.txt` で `utterance` と `controlled_answer` が一致するか確認する。
3. LLM生徒発話の品質を改善する。
   - 「生徒AIとして」などメタ発話が出ないようにする。
   - 「教師」「先生」ラベル混入をさらに除去する。
   - `答え: わかりません` が正答扱いになるケースを避ける。
4. 伝達AIのLLM出力をJSON schema寄りに安定化する。
5. 10人、20人クラスで講義設計がどう変わるか比較する。
6. 発表・論文用には「認知モデルで制御された生徒AIが、クラス全体の授業設計入力として使えるか」を中心にまとめる。


