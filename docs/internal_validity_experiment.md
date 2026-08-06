# 内部妥当性評価 実験手順

最終更新: 2026-08-06

## 目的

この実験は、生徒AIが実際の生徒に似ていることを直接証明するものではない。

目的は、教育シミュレーション用の代理生徒として、内部状態を操作したときに一貫した反応が得られるかを確認することである。研究上の主張は、実生徒の完全な再現ではなく、**理解度・誤概念・個人特徴を制御可能な学習者代理として使えるか**に限定する。

## 研究上の位置づけ

本研究では、生徒AIを「教師AIの授業設計を検証するための制御可能なクラス環境」として使う。

そのため、内部妥当性評価では次を確認する。

1. 理解度を上げると正答確率・正答率が上がるか。
2. 問題難易度を上げると、同じ理解度でも正答確率が下がるか。
3. 誤概念を入れると、関連スキルの問題で正答確率が下がるか。
4. 特定スキルだけ低くすると、そのスキルの問題で弱点が出るか。
5. 個人特徴を変えると、発話上の見え方が変わるか。
6. LLM発話が教師発話を混ぜず、生徒1ターンとして観察可能か。

## 使う認知モデル

現在の主実験では `bkt_irt` を使う。

実装:

```text
src/cognitive_model.py
BKTIRTCognitiveModel
```

このモデルは、実データでパラメータ推定した厳密なBKT/IRTではない。教育シミュレーション用に、BKT/IRTの考え方を取り入れた制御モデルである。

主な構成要素:

| 要素 | 意味 |
| --- | --- |
| skill_score | スキル別理解度 |
| overall_score | 単元全体の理解度 |
| difficulty_score | 問題難易度 |
| guess_probability | 未習得でも偶然正答する確率 |
| slip_probability | 習得済みでも誤答する確率 |
| misconception_penalty | 誤概念による正答確率低下 |
| self_efficacy / motivation | 正答確率への小補正と発話特徴 |

## 実験で確認すること

| 実験 | 操作する条件 | 期待する結果 |
| --- | --- | --- |
| 学習曲線 | 理解度・スキル習得度を0-100で変化 | 潜在的な知識状態が高いほど正答率が上がる |
| 難易度感度 | difficultyを比較 | 同じ理解度でも難しい問題ほど正答確率が下がる |
| 誤概念感度 | 誤概念あり/なしを比較 | 関連問題で正答確率に差が出る |
| スキル別弱点 | 特定スキルだけ低くする | 該当問題の正答確率が下がる |
| 個人特徴 | 自己効力感、質問傾向、意欲、Big Fiveを変える | 発話特徴が変わる |
| 発話形式 | LLM出力を後処理する | 教師発話が混入せず、生徒1ターンになる |
| モデル比較 | legacy と bkt_irt を比較 | bkt_irtで難易度・guess・slipの影響が確認できる |

## 推奨実行方法

Notebookに依存せず、次のスクリプトで内部妥当性評価を出力できる。

```bash
python scripts/run_internal_validity_experiment.py
```

Windowsローカルでは次でもよい。

```powershell
py scripts\run_internal_validity_experiment.py
```

Colabではrepo rootで以下を実行する。

```python
!python scripts/run_internal_validity_experiment.py
```

出力ファイル:

```text
data/assessments/student_ai_internal_validity_summary.txt
data/assessments/student_ai_internal_validity_for_codex.txt
data/assessments/cognitive_model_comparison_for_codex.txt
```

Codex/ChatGPTに結果確認を依頼するときは、まず次を添付する。

```text
data/assessments/student_ai_internal_validity_for_codex.txt
```

legacy と bkt_irt の比較を見たい場合は、次も添付する。

```text
data/assessments/cognitive_model_comparison_for_codex.txt
```

## 実行オプション

### 生徒IDを変える

```bash
python scripts/run_internal_validity_experiment.py --student-id S002
```

### テストを変える

```bash
python scripts/run_internal_validity_experiment.py --test-id linear_equation_20q_001
```

### 理解度刻みを変える

```bash
python scripts/run_internal_validity_experiment.py --understanding-levels 0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100
```

### LLM発話サンプルも使う

LLMロードが重いので、通常はmockでよい。発話自然性を見たいときだけ使う。

```bash
python scripts/run_internal_validity_experiment.py --use-llm
```

## Colab Notebookで実行する場合

既存Notebookを使う場合は、次を実行する。

```text
notebooks/student_ai_colab.ipynb
notebooks/student_ai_presentation_experiment.ipynb
```

ただし、論文用の再現性を優先する場合は、Notebookより `scripts/run_internal_validity_experiment.py` を優先する。

## 判定基準

### 1. 学習曲線

見る項目:

- `cognitive_learning_curve`
- `Learning Curve`
- `accuracy_gain_from_min_to_max`
- `probability_gain_from_min_to_max`

最低限の期待:

- 理解度0より理解度100の正答率が高い
- 平均正答確率が大きく上昇している
- 理解度と正答率は完全一致しない
- 低理解度でも guess により一部正答し、高理解度でも slip により一部誤答する

### 2. 難易度感度

見る項目:

- `Difficulty Breakdown`
- `average_correct_probability`
- `average_guess_probability`
- `average_slip_probability`
- `difficulty_probability_gap`

最低限の期待:

- easy より hard の正答確率が低い
- guess/slip が出力されている
- 同じ理解度でも問題難易度が結果に影響している

### 3. 誤概念感度

見る項目:

- `misconception_sensitivity`
- `related_probability_gap`
- `related_accuracy_with_misconception`
- `related_accuracy_without_misconception`

最低限の期待:

- 関連問題で、誤概念なし条件の方が正答確率が高い
- 低中理解度で差が出る
- 高理解度では差が小さくなる

### 4. スキル別弱点

見る項目:

- `skill_specific_weakness`
- `weak_skill_probability`
- `baseline_probability`
- `target_probability_drop`

最低限の期待:

- 弱点スキル条件で基準条件より正答確率が下がる
- どのスキルを弱くしたかが結果表に残る

### 5. 個人特徴の発話反映

見る項目:

- `personality_observable_separation`
- `Utterance Samples`
- `char_count`
- `question_mark_count`
- `uncertainty_marker_count`

最低限の期待:

- 低自己効力感の生徒は不安・迷いが出る
- 質問傾向が高い生徒は確認や質問が出やすい
- 低モチベーションの生徒は短い返答になりやすい
- 性格サンプルでは正答を固定し、正誤差と性格差を混ぜない

### 6. 生徒1ターン発話

見る項目:

- `one_turn_student_response`
- `has_teacher_label`

最低限の期待:

- `has_teacher_label` が false
- 教師発話が混入していない
- 解答形式が `答え: x = ...` に統一されている

## 論文での書き方

使える表現:

```text
本実験では、生徒AIの内部状態を操作したときに、正答率、難易度の影響、誤概念の影響、スキル別弱点、発話特徴が設計意図と整合するかを確認した。理解度は正答率そのものではなく、正答・誤答を生成する潜在的な知識状態として扱った。
その結果、生徒AIは一次方程式学習に限定した教育シミュレーション用代理生徒として、内部妥当性を満たすことが確認された。
```

避ける表現:

```text
生徒AIは実際の生徒を再現している。
生徒AIは人間学習者の代替として妥当である。
実クラスと同じ分布を再現できた。
```

## 限界

この実験では、実際の生徒データとの比較は行わない。

そのため、実際の生徒集団との一致、実クラスのテスト分布の再現、実際の教育効果は検証していない。

今後の課題として、実クラスの正誤データや授業中発話を用いた外的妥当性評価を行う。

## 次の段階

内部妥当性評価が通ったら、次は複数生徒クラスの評価に進む。

次に確認すること:

1. 3人、10人、20人、30人でクラス生成・集計ができるか。
2. 低理解・中理解・高理解の分布を設定できるか。
3. クラス条件の違いが伝達AI・講義設計AIの入力に反映されるか。
