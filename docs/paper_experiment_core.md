# 論文用 実験コア設計

作成日: 2026-07-23

## 研究の立場

本研究では、生徒AIを人間学習者の完全な再現として扱わない。

また、現時点では実クラスのテスト結果や授業中発話データを持たないため、実際の生徒集団との一致を検証する外的妥当性は扱わない。

本研究で扱うのは、教育シミュレーション用の代理生徒としての内部妥当性である。

```text
内部妥当性:
理解度、誤概念、スキル弱点、個人特徴を操作したとき、
生徒AIの正答率、誤答傾向、発話特徴が設計意図通りに変化するか。
```

論文での主張は次に限定する。

```text
一次方程式学習において、外部状態として定義した理解度・誤概念・個人特徴を操作することで、
教育シミュレーション用の代理生徒として一貫した反応を生成できることを示す。
```

## 研究の問い

### RQ1: 理解度操作の内部妥当性

生徒AIの理解度・スキル習得度を0から100まで変化させたとき、一次方程式テストの正答率は段階的に上昇するか。

ここでの理解度は、正答率そのものではなく、問題解決を左右する潜在的な知識状態として扱う。正答・誤答は、知識状態、問題難易度、誤概念、guess/slip によって生成される観測結果である。

評価指標:

- `understanding`
- `correct_count`
- `accuracy`
- `average_correct_probability`
- `cognitive_learning_curve`

期待される結果:

- 理解度・スキル習得度が高いほど正答率が高い
- 平均正答確率が単調に上昇する
- ただし、理解度と正答率は完全一致しない
- 高理解度でも slip による誤答があり、低理解度でも guess による正答がある

### RQ2: 誤概念操作の内部妥当性

同じ理解度でも、誤概念あり条件では関連問題の正答確率が下がるか。

評価指標:

- `all_probability_gap`
- `related_probability_gap`
- `related_accuracy_with_misconception`
- `related_accuracy_without_misconception`
- `misconception_sensitivity`

期待される結果:

- 全問平均よりも、関連問題に限定した差分の方が大きい
- 低中理解度では誤概念の影響が大きい
- 高理解度では誤概念の影響が小さくなる

### RQ3: スキル別弱点の内部妥当性

特定スキルだけを弱くしたとき、該当スキル問題の正答確率が基準条件より下がるか。

評価指標:

- `weak_skill`
- `weak_skill_probability`
- `baseline_probability`
- `target_probability_drop`
- `skill_specific_weakness`

期待される結果:

- 弱点化したスキルの問題で正答確率が下がる
- スキル別の弱点がテスト結果に反映される

### RQ4: 個人特徴の発話反映

自己効力感、質問傾向、モチベーション、Big Five の違いが、発話特徴として観察できるか。

評価指標:

- `char_count`
- `line_count`
- `question_mark_count`
- `uncertainty_marker_count`
- `has_answer_label`
- `has_teacher_label`
- `personality_observable_separation`

期待される結果:

- 自己効力感が低い生徒は不安や迷いを出しやすい
- 質問傾向が高い生徒は確認や質問を出しやすい
- モチベーションが低い生徒は短い返答になりやすい
- 誠実性が高い生徒は途中式を出しやすい

### RQ5: 生徒1ターン発話としての制御

LLM出力が教師発話や会話台本を混ぜず、生徒1ターンの観察可能情報として扱えるか。

評価指標:

- `has_teacher_label`
- `one_turn_student_response`

期待される結果:

- `教師:`、`先生:` などの教師発話が残らない
- 生徒の1ターン発話としてログ・伝達AI・教師AIへ渡せる

### RQ6: 認知モデル比較

従来の理解度中心モデルと、BKT/IRT寄りの認知モデルを比較したとき、後者は問題難易度、guess、slipを反映した正答確率を生成できるか。

評価指標:

- `legacy_average_correct_probability`
- `bkt_irt_average_correct_probability`
- `probability_delta`
- `accuracy_delta`

期待される結果:

- BKT/IRT寄りモデルでは、同じ理解度でも問題難易度の影響が入る
- 低理解度でも guess により正答確率が残る
- 高理解度でも slip により正答確率が100%にはならない
- 従来モデルより、理解度と正答率を同一視しない説明がしやすい

## 実験実行方法

Colabでは `notebooks/student_ai_colab.ipynb` の生徒AI評価セルを実行する。

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
    use_mock_model=False,
)

export_student_ai_evaluation(result)
export_student_ai_evaluation_for_codex(result)
```

Codex/ChatGPTに共有する出力:

```text
data/assessments/student_ai_evaluation_for_codex.txt
```

## 出力の見方

### Summary

見る項目:

- `accuracy_gain_from_min_to_max`
- `probability_gain_from_min_to_max`
- `weakest_skill_condition`
- `internal_validity_score`
- `raw_internal_score`
- `evidence_level`

`evidence_level` は `internal_validity_only` である。これは、実際の生徒との一致ではなく、内部状態操作に対する一貫性を示す。

### Internal Validity Evaluation

5つの評価軸を確認する。

| 評価軸 | 対応するRQ |
| --- | --- |
| `cognitive_learning_curve` | RQ1 |
| `misconception_sensitivity` | RQ2 |
| `skill_specific_weakness` | RQ3 |
| `personality_observable_separation` | RQ4 |
| `one_turn_student_response` | RQ5 |
| `learning_curve_comparison` | RQ6 |

### Learning Curve

理解度・スキル習得度と正答率の関係を見る。

論文では、理解度を横軸、正答率または平均正答確率を縦軸にしたグラフとして使える。ただし、理解度を正答率そのものとは解釈しない。理解度は潜在的な知識状態であり、正答率は問題難易度、誤概念、guess/slip を通じて観測される結果である。

### Misconception Comparison

誤概念あり/なしの差を見る。

特に重要なのは `related_probability_gap` である。全問平均では誤概念の影響が薄まるため、関連問題に限定した差分を見る。

### Skill Breakdown

スキル別弱点の影響を見る。

特に重要なのは `target_probability_drop` である。これは、基準条件と比べて、弱点スキル条件でどれだけ正答確率が下がったかを示す。

### Utterance Samples

個人特徴が発話に反映されているかを見る。

性格差を見るサンプルでは正答を固定し、正誤差と性格差が混ざらないようにする。

### Cognitive Model Comparison

従来モデルとBKT/IRT寄りモデルの学習曲線を比較する。

論文では、同じ理解度設定に対して、従来モデルとBKT/IRT寄りモデルの平均正答確率を重ねたグラフとして使える。BKT/IRT寄りモデルでは、問題難易度、guess、slipを加味するため、理解度が正答率へ直接変換されているわけではないことを示しやすい。

## 論文で主張できること

- 生徒AIの理解度を操作すると、正答率が段階的に変化する
- 理解度を正答率そのものではなく、正答行動を生む潜在的な知識状態として扱える
- 誤概念を持たせると、関連問題で正答確率が下がる
- 特定スキルを弱くすると、該当問題の正答確率が下がる
- 個人特徴を変えると、発話特徴が変わる
- LLM出力を生徒1ターン発話として制御できる
- 教育シミュレーション用代理生徒としての内部妥当性を確認できる
- 従来モデルとBKT/IRT寄りモデルを比較し、認知モデル設計の違いを実験結果として示せる

## 論文で主張しないこと

- 実際の生徒の学習過程を再現した
- 実クラスのテスト結果分布を再現した
- 実際の教育効果を証明した
- LLMが内部的に理解度や誤概念を持っている
- 人間学習者の完全な代替ができる

## 限界

本研究は内部妥当性の検証に限定される。

実際の生徒との外的妥当性を確認するには、実クラスの問題別正誤、スキル別正答率、誤答内容、授業中発話などのデータが必要である。

今後は、実クラスデータとAI生徒集団の分布を比較し、平均、標準偏差、問題別正答率、スキル別正答率、誤答パターンの一致度を評価する。

## 最小実験セット

内部妥当性を論文に載せるための最小実験は次である。

1. 理解度0-100の学習曲線
2. 誤概念あり/なしの関連問題比較
3. スキル別弱点条件の比較
4. 個人特徴別の発話サンプル比較
5. 生徒1ターン発話の形式チェック

この5つを `student_ai_colab.ipynb` で出力し、結果を `student_ai_evaluation_for_codex.txt` にまとめる。
