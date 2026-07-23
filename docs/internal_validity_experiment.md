# 内部妥当性評価 実験手順

作成日: 2026-07-23

## 目的

この実験は、生徒AIが実際の生徒に似ているかを検証するものではない。

目的は、教育シミュレーション用の代理生徒として、内部状態を操作したときに一貫した反応が得られるかを確認することである。

## 実験で確認すること

| 実験 | 操作する条件 | 期待する結果 |
| --- | --- | --- |
| 学習曲線 | 理解度・スキル習得度を0-100で変化 | 潜在的な知識状態が高いほど正答率が上がる |
| 誤概念感度 | 誤概念あり/なしを比較 | 関連問題で正答確率に差が出る |
| スキル別弱点 | 特定スキルだけ低くする | 該当問題の正答確率が下がる |
| 個人特徴 | 自己効力感、質問傾向、意欲、Big Fiveを変える | 発話特徴が変わる |
| 発話形式 | LLM出力を後処理する | 教師発話が混入せず、生徒1ターンになる |

## 実行するNotebook

```text
notebooks/student_ai_colab.ipynb
```

実行後、次のファイルを確認する。

```text
data/assessments/student_ai_evaluation_for_codex.txt
```

## Colabでの実行コード

```python
from src.experiment import (
    export_student_ai_evaluation,
    export_student_ai_evaluation_for_codex,
    run_student_ai_evaluation,
)

student_ai_evaluation = run_student_ai_evaluation(
    student_id="S002",
    test_id="linear_equation_20q_001",
    understanding_levels=list(range(0, 101, 10)),
    use_mock_model=False,
)

summary_path = export_student_ai_evaluation(student_ai_evaluation)
codex_path = export_student_ai_evaluation_for_codex(student_ai_evaluation)

print(summary_path)
print(codex_path)
print(student_ai_evaluation["summary"])
```

LLMロードが重い場合は、まず `use_mock_model=True` で構造確認を行う。

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

### 2. 誤概念感度

見る項目:

- `misconception_sensitivity`
- `related_probability_gap`
- `related_accuracy_with`
- `related_accuracy_without`

最低限の期待:

- 関連問題で、誤概念なし条件の方が正答確率が高い
- 低中理解度で差が出る
- 高理解度では差が小さくなる

### 3. スキル別弱点

見る項目:

- `skill_specific_weakness`
- `weak_skill_probability`
- `baseline_probability`
- `target_probability_drop`

最低限の期待:

- 弱点スキル条件で基準条件より正答確率が下がる
- どのスキルを弱くしたかが結果表に残る

### 4. 個人特徴の発話反映

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

### 5. 生徒1ターン発話

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
本実験では、生徒AIの内部状態を操作したときに、正答率、誤概念の影響、スキル別弱点、発話特徴が設計意図と整合するかを確認した。理解度は正答率そのものではなく、正答・誤答を生成する潜在的な知識状態として扱った。
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
