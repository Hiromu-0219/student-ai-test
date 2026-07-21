# 論文用 実験コア設計

作成日: 2026-07-21

## 研究の中心

本研究の中心は、教育シミュレーションにおいて、AI生徒を人間学習者の完全な代替として使うことではない。

主張する範囲は次に限定する。

> 一次方程式の学習場面において、理解度、誤概念、個人特徴を外部状態として制御した生徒AIが、教師AIの授業設計を検証するための「限定的な学習者代理」として利用可能かを検証する。

## なぜこの再設計が必要か

単に「LLMが生徒らしく話す」だけでは、人間に置き換える妥当性は弱い。

妥当性を出すには、少なくとも次の性質を確認する必要がある。

- 理解度が高いほど正答率が上がる
- 誤概念があると、関連問題で誤答しやすくなる
- 理解度が上がると、誤概念の影響が弱まる
- 生徒ごとの弱点スキルが結果に反映される
- 自信、質問傾向、意欲などの個人特徴が発話に反映される
- 教師AIや伝達AIは、内部パラメータではなく授業中に観察できる情報から判断する

## 実験の問い

### RQ1: 認知モデルの妥当性

生徒AIの理解度を 0 から 100 まで変化させたとき、一次方程式テストの正答率は段階的に上昇するか。

見る指標:

- understanding
- correct_count
- accuracy
- average_correct_probability

### RQ2: 誤概念の妥当性

同じ理解度でも、誤概念あり条件では関連問題の正答確率が下がるか。

見る指標:

- accuracy_with_misconception
- accuracy_without_misconception
- probability_gap

期待する形:

- 低理解度では誤概念の影響が大きい
- 高理解度では誤概念の影響が小さくなる

### RQ3: 個人特徴の妥当性

同じ問題に対して、自己効力感、質問傾向、意欲、Big Five の違いが発話特徴として現れるか。

見る指標:

- 文字数
- 行数
- 質問記号の数
- 不安・迷いを示す表現
- 途中式の有無

### RQ4: 観察可能情報に基づく推定

伝達AIが、内部状態を直接見ずに、授業中に観察できる生徒発話や正誤だけから生徒状態を推定できるか。

見る指標:

- 観察イベントに内部状態が混入していないか
- 伝達AIの推定結果
- 教師AIに渡されるクラス要約

## 現在の実装で出す評価

`src/experiment/student_ai_evaluation.py` では、次をまとめて出力する。

- Learning Curve
- Misconception Comparison
- Skill Breakdown
- Utterance Samples
- Human Replacement Validity

Colabで実行する主なコード:

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
    use_mock_model=False,  # LLMを使う場合
)

export_student_ai_evaluation(result)
export_student_ai_evaluation_for_codex(result)
```

Codex/ChatGPTに共有する場合は、次のファイルを添付する。

```text
data/assessments/student_ai_evaluation_for_codex.txt
```

## Human Replacement Validity の評価軸

現時点では、妥当性を次の5軸で見る。

| 評価軸 | 意味 |
| --- | --- |
| cognitive_learning_curve | 理解度上昇に対して正答確率が自然に上がるか |
| misconception_sensitivity | 誤概念が関連問題の誤答に反映されるか |
| skill_specific_weakness | 弱点スキルを変えると結果が変わるか |
| personality_observable_separation | 個人特徴が発話特徴として観察できるか |
| one_turn_student_response | 生徒1ターンの発話として扱えるか |

この評価は、人間との完全一致を示すものではない。

ただし、教育シミュレーションで教師AIの授業設計を比較するための代理生徒として、どの程度制御可能かを示す根拠になる。

## 論文で主張しないこと

- 人間の学習過程を完全に再現したとは主張しない
- 実際の教育効果を証明したとは主張しない
- 教師AIの授業が現実の教師より優れているとは主張しない
- LLM単体が生徒の認知状態を持っているとは主張しない

## 論文で主張できる可能性があること

- 生徒AIの知識状態を外部認知モデルで制御できる
- 誤概念と理解度の関係を条件として操作できる
- 個人特徴を発話スタイルに反映できる
- 伝達AIが観察可能情報からクラス状態を要約できる
- クラス状態の違いによって、教師AIの授業構成を変化させられる

## 次に必要な検証

1. 複数生徒クラスで同じ評価を行う
2. 伝達AIが観察可能情報だけで分類できるかを評価する
3. 教師AIの授業構成がクラス状態によって変わるかを比較する
4. LLM使用条件とモック条件で、発話の自然性と安定性を比較する
5. 可能なら人間評価者に、生徒発話の自然性・個人特徴の見え方を評価してもらう
