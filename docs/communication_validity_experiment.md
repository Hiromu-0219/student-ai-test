# 伝達AIの推定妥当性実験

最終更新: 2026-08-07 15:51:27 JST

## 目的

第3段階では、伝達AIが生徒AIの内部パラメータを直接見ずに、授業中に観察できる情報だけから教師AIに渡す生徒情報を推定できるかを検証する。

この実験は、教育シミュレーション全体における次の接続部分を確認する。

```text
生徒AIの内部状態
  -> 生徒AIの発話・正誤・反応として外に出る
  -> 観察可能情報だけを伝達AIへ渡す
  -> 伝達AIが生徒個人とクラス全体を要約する
  -> 教師AI・講義設計AIが授業方針に使う
```

## なぜ必要か

教師は実際の授業中、生徒の内部パラメータを直接見ることはできない。見えるのは発話、無反応、正誤、途中式、質問の有無、反応の遅さなどである。

そのため、教育シミュレーションとして成立させるには、伝達AIも内部状態を覗くのではなく、観察可能な情報から粗く推定する必要がある。

## 入力と隠れラベル

伝達AIに渡す入力は `src/observer/observation_filter.py` の `ObservableEvent` から作る。

伝達AIに渡すもの:

- `student_id`
- 生徒の発話
- 授業中に観察できるイベント情報

伝達AIに渡さないもの:

- `knowledge_state`
- `self_efficacy`
- `question_tendency`
- `motivation`
- `big_five`
- `misconceptions`
- `correct_probability`

ただし、評価時には隠れラベルとして内部状態を参照し、推定結果と比較する。

## 評価指標

### 1. observable_input_only

伝達AIに渡したデータに内部パラメータが混入していないかを見る。

### 2. individual_trait_estimation

生徒ごとに、以下の粗い3段階ラベルが一致するかを見る。

- self_efficacy
- question_tendency
- motivation
- neuroticism

`very_low` と `low` は `low`、`very_high` と `high` は `high` に圧縮して評価する。

### 3. profile_estimation

A/B/C/Dの粗い生徒タイプが一致するかを見る。

- A: 自信が低い、または不安が高い
- B: 丁寧で協力的
- C: 発話が短い、質問が少ない、意欲が低い
- D: 自信と意欲が高い

### 4. class_level_count_agreement

個人単位の完全一致だけでなく、クラス全体として low / medium / high の人数分布が近いかを見る。

この研究の目的は個人診断ではなく、クラス全体を見て講義を設計することなので、クラス分布の一致を重視する。

### 5. priority_student_recall

教師が注意すべき生徒を、伝達AIがどれだけ拾えるかを見る。

ここでは、低自信、低意欲、質問しにくさ、高不安、低理解、誤答を持つ生徒を優先対象とする。

## 実行方法

```bash
python scripts/run_communication_validity_experiment.py
```

出力:

```text
data/assessments/communication_validity_for_codex.txt
```

## 主張範囲

この実験で主張できるのは、伝達AIが観察可能な発話から教育上使える粗い状態推定を行えるかである。

実際の人格や心理状態を正確に診断できること、あるいは実際の人間教師の観察と同等であることは、この実験だけでは主張しない。


