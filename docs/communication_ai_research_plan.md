# 伝達AI研究計画

最終更新: 2026-08-07 15:51:27 JST

## 研究上の役割分担

このリポジトリでは、研究の主対象を伝達AIに置く。

```text
生徒AI
  統制されたGround Truth Stateを持ち、回答・発話・反応ログを生成する実験基盤

伝達AI
  Observable EventだけからTeacher Belief Stateを推定・要約する主研究対象

教師AI
  伝達AIの出力が授業判断に使えるかを見る下流評価機能
```

生徒AIの認知モデル、誤概念、スキル弱点、個人特徴、複数生徒クラスは削除しない。これらは、伝達AIを評価するための統制可能なシミュレーション基盤として扱う。

## 3層の分離

```text
Ground Truth State
  シミュレーション内部だけが知る真の学習者状態

Observable State
  回答、正誤、発話、反応時間、質問、途中式など、授業中に観察できる情報

Teacher Belief State
  Observable Stateから伝達AIが推定した教師側の生徒理解
```

伝達AIと教師AIは、Ground Truth Stateを直接参照しない。Ground Truth Stateは評価時の正解ラベルとしてのみ使う。

## 現在すでに研究目的を満たしている部分

- `src/cognitive_model.py`: 生徒AIの正答確率と誤答を制御する認知モデル
- `src/student_ai.py`, `src/student_agent.py`: 生徒AIの回答・発話生成
- `src/observer/observation_filter.py`: 内部状態を除外した観察イベント
- `src/observer/trait_classifier.py`: 伝達AIの個人特徴推定
- `src/teacher/belief_manager.py`: 観察から教師信念を更新する既存基盤
- `src/teacher/lesson_planner.py`: 教師信念から授業構成を作る下流機能
- `src/experiment/communication_validity.py`: 単発の伝達AI推定妥当性チェック
- `src/experiment/lesson_design_validity.py`: 授業設計AIの下流評価

## 試作・ルールベースに留まっている部分

- `CommunicationAI` は現在ルールベースであり、LLM版 `LLMCommunicationAI` は比較対象として未整備
- 誤概念推定は、発話・誤答内の語句と対象スキルからの候補検出である
- 反応時間は現時点ではシミュレーション上の再現可能な生成値であり、実測値ではない
- 教師AIは授業計画の下流評価用であり、長期学習効果の最適化までは扱っていない

## 不足していた部分と今回の追加

RQ1を評価するため、`src/experiment/rq1_communication_ai.py` を追加した。

追加した機能:

- Ground Truth Stateから複数問題に対するObservable Eventを生成
- Observable EventだけからTeacher Belief Stateを推定
- `stats_baseline`, `rule_based_communication_ai`, `enhanced_communication_ai` を同一データで比較
- 観察情報のアブレーション
- スキル習熟度、全体理解度、誤概念、個人特徴、確信度をGround Truthと比較
- JSONとtxtの両方で結果を出力
- 失敗例に真の状態、推定状態、根拠イベント、追加観察候補を含める

## RQ1の評価対象

### スキル習熟度

- MAE
- RMSE
- スキル別誤差
- 生徒別誤差
- 観察数と誤差の関係

### 全体理解度

- MAE
- 順位相関
- high / medium / low の分類精度

### 誤概念

- Precision
- Recall
- F1
- 誤概念別の検出性能

### 個人・行動特徴

- 自己効力感
- 質問傾向
- モチベーション
- 不安傾向

### 確信度

- Brier score
- Expected Calibration Error
- confidence binごとの正解率

## 比較する伝達方式

```text
stats_baseline
  正誤だけを使う単純統計ベースライン

rule_based_communication_ai
  既存CommunicationAIを使うルールベース伝達AI

enhanced_communication_ai
  根拠イベント、反証イベント、情報不足、追加観察を構造化して出す拡張伝達AI
```

## 観察情報アブレーション

```text
correctness_only
correctness_answer
correctness_answer_utterance
correctness_answer_response_time
all_observable
```

## 実行方法

```bash
python scripts/run_rq1_communication_ai_experiment.py
```

出力:

```text
data/assessments/rq1_communication_ai.json
data/assessments/rq1_communication_ai_for_codex.txt
```

## 現時点の主張範囲

この実験で確認できるのは、シミュレーション内部で統制された生徒AIに対して、伝達AIが観察可能ログから状態推定できるかという内部妥当性である。

実際の人間学習者の心理状態を正確に推定できることや、実教室で同じ性能が出ることはまだ主張しない。


