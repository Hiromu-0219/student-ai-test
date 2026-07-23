# 参考文献・参考資料対応表

作成日: 2026-07-23

## 目的

この文書は、生徒AIの理解度モデル・正答確率モデル・教育シミュレーション設計で参考にした先行研究や参考資料を、設計要素ごとに対応づけるためのメモである。

論文執筆時には、この表をもとに「どの設計判断がどの研究領域の考え方に基づくか」を説明する。

## 対応表

| 本研究での設計要素 | 参考にした考え方 | 対応する文献・資料 | 本研究での使い方 |
| --- | --- | --- | --- |
| 理解度を正答率そのものとみなさない | 知識状態は潜在変数であり、正答・誤答は観測変数として扱う | Corbett & Anderson (1995), BKT | `knowledge_state` やスキル習得度を内部状態として持ち、テストの正誤はそこから生成される観測結果として扱う |
| スキルごとの習得度 | Knowledge component / skill mastery | Corbett & Anderson (1995), Knowledge Tracing survey | 一次方程式を `can_transpose_terms`, `can_divide_by_coefficient` などのスキルに分解する |
| 低理解でも正答する場合 | Guess parameter | BKT, IRT 3PL | 未習得でも偶然・部分理解で正答する確率を `guess` として扱う |
| 高理解でも誤答する場合 | Slip parameter | BKT | 習得していても計算ミス、読み違い、不注意で間違える確率を `slip` として扱う |
| 授業や練習による理解度更新 | Learn / transition probability | BKT | 将来的に、授業後や演習後にスキル習得度が少しずつ上がる更新規則として使う |
| 問題難易度による正答確率の変化 | Ability and item difficulty | IRT / Rasch / 1PL | 生徒のスキル習得度と問題難易度の差で正答確率が変わるようにする |
| 問題によって識別力が違う | Item discrimination | IRT 2PL | 将来的に、理解度差が出やすい問題と出にくい問題を分ける拡張候補にする |
| 選択式・偶然正答の扱い | Guessing / lower asymptote | IRT 3PL | 低能力でも正答率が0にならない説明に使う |
| 学習履歴から次の正答確率を予測する発想 | Knowledge Tracing | DKT, Knowledge Tracing survey | 本研究では深層学習モデルとしては使わず、研究背景・発展形として位置づける |
| 解釈可能性を優先する設計 | BKTは解釈可能な知識追跡モデルとして使われる | BKT関連研究、Knowledge Tracing survey | LLMに正誤判断を任せず、外部認知モデルで制御する根拠にする |

## 本研究への落とし込み

本研究では、BKTやIRTを厳密な統計モデルとして推定しているわけではない。実クラスの大規模な解答ログがないため、パラメータ推定ではなく、教育シミュレーション用の解釈可能な近似モデルとして取り入れる。

現在の設計では、理解度・スキル習得度を次のように扱う。

```text
理解度・スキル習得度 = 生徒AIの潜在的な知識状態
正答・誤答 = 知識状態、問題難易度、誤概念、guess/slip によって生成される観測結果
```

正答確率の考え方:

```text
P(correct) =
  ability_skill_match
  + guess
  - slip
  - misconception_penalty
  + affective_adjustment
```

BKT的な解釈:

```text
P(correct) = P(learned) * (1 - slip) + (1 - P(learned)) * guess
```

IRT的な解釈:

```text
P(correct) = sigmoid(skill_mastery - problem_difficulty)
```

このため、本研究では「理解度が上がると正答率も上がる」という相関は作るが、「理解度=正答率」とは主張しない。

## 論文での書き方候補

本研究では、生徒AIの理解度を正答率そのものではなく、問題解決を左右する潜在的な知識状態として定義する。正答・誤答は、知識状態、問題難易度、誤概念、guess/slip によって生成される観測結果として扱う。この考え方は、学習者の知識状態を潜在変数として扱う Bayesian Knowledge Tracing や、能力と項目難易度の関係から正答確率を表す Item Response Theory の考え方を参考にしている。ただし、本研究では実データからパラメータ推定を行うのではなく、教育シミュレーション用の制御可能で解釈可能な近似モデルとして利用する。

## 参考文献候補

### Bayesian Knowledge Tracing

- Corbett, A. T., & Anderson, J. R. (1995). Knowledge tracing: Modeling the acquisition of procedural knowledge. User Modeling and User-Adapted Interaction, 4, 253-278. https://doi.org/10.1007/BF01099821
- Yudelson, M. V., Koedinger, K. R., & Gordon, G. J. (2013). Individualized Bayesian Knowledge Tracing Models. In Artificial Intelligence in Education.
- Baker, R. S., Corbett, A. T., & Aleven, V. (2008). More Accurate Student Modeling Through Contextual Estimation of Slip and Guess Probabilities in Bayesian Knowledge Tracing.

### Knowledge Tracing全般

- Abdelrahman, G., Wang, Q., & Nunes, B. (2023). Knowledge Tracing: A Survey. ACM Computing Surveys, 55(11), Article 224. https://doi.org/10.1145/3569576
- Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L. J., & Sohl-Dickstein, J. (2015). Deep Knowledge Tracing. Advances in Neural Information Processing Systems, 28, 505-513.

### Item Response Theory

- Rasch, G. (1960). Probabilistic Models for Some Intelligence and Attainment Tests.
- Birnbaum, A. (1968). Some Latent Trait Models and Their Use in Inferring an Examinee's Ability. In F. M. Lord & M. R. Novick, Statistical Theories of Mental Test Scores.
- Lord, F. M. (1980). Applications of Item Response Theory to Practical Testing Problems.

## 参考Web資料

- BKT overview: https://www.cs.williams.edu/~iris/res/bkt-balloon/index.html
- CiNii entry for Corbett & Anderson (1995): https://cir.nii.ac.jp/crid/1364233269756361984
- Columbia University overview of IRT: https://www.publichealth.columbia.edu/research/population-health-methods/item-response-theory
- DBLP entry for Deep Knowledge Tracing: https://dblp.org/rec/conf/nips/PiechBHGSGS15

## 注意

現時点の本研究では、実際の生徒データを用いたBKT/IRTパラメータ推定は行っていない。そのため、論文では「BKT/IRTを実装・推定した」とは書かず、「BKT/IRTの考え方を参考に、教育シミュレーション用の解釈可能な近似モデルとして設計した」と書く。
