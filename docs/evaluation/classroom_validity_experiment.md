# 複数生徒クラス妥当性評価

最終更新: 2026-08-07 15:51:27 JST

## 目的

この実験は、生徒AIを1人単位ではなく、クラス集団として扱えるかを確認するための第2段階である。

研究目的は、教師AIがクラス全体を見て授業方針を決めることである。そのため、生徒AIが個別に動くだけでは不十分で、複数生徒にしたときに次の情報が見える必要がある。

1. クラス人数が変わっても同じ形式で集計できる。
2. 低理解・中理解・高理解の分布が見える。
3. 誤概念を持つ生徒の人数が見える。
4. 自己効力感、質問傾向、モチベーションなどの個人特徴分布が見える。
5. 同じ代表問題を出したとき、クラス内の生徒ごとに予測正答率が変わる。
6. 教師AIへ渡せるクラスリスクが抽出できる。

## 評価対象

現在の標準評価では、次の4クラスを比較する。

| class_id | 人数 | 目的 |
| --- | ---: | --- |
| class_3_basic | 3 | 小規模デバッグ用 |
| class_10_mixed | 10 | クラス要約の試験用 |
| class_20_mixed | 20 | 標準的な複数生徒実験用 |
| class_30_mixed | 30 | 大人数クラスへの拡張確認用 |

`class_30_mixed` のために、`S021` から `S030` までの合成生徒データを追加している。

## 実行方法

Notebookに依存せず、次のスクリプトで実行できる。

```bash
python scripts/run_classroom_validity_experiment.py
```

Windowsローカルでは次でもよい。

```powershell
py scripts\run_classroom_validity_experiment.py
```

Colabではrepo rootで以下を実行する。

```python
!python scripts/run_classroom_validity_experiment.py
```

出力ファイル:

```text
data/assessments/classroom_validity_for_codex.txt
```

Codex/ChatGPTに確認させる場合は、このtxtを添付する。

## 出力で見る項目

### Class Comparison

| 項目 | 意味 |
| --- | --- |
| student_count | クラス人数 |
| average_score | クラス平均理解度 |
| score_std | 理解度のばらつき |
| low_count | 低理解層の人数 |
| medium_count | 中理解層の人数 |
| high_count | 高理解層の人数 |
| misconception_count | 誤概念を持つ生徒数 |
| trait_variety | 個人特徴分布の多様さ |
| probe_accuracy | 代表問題での予測正答率 |
| probe_probability | 代表問題での平均正答確率 |
| recommended_use | そのクラスの用途 |

### Class Details

各クラスについて、以下を確認する。

- `score_buckets`
- `trait_counts`
- `probe_summary`
- `visible_class_risks`

`visible_class_risks` は教師AIに渡す前段のクラスリスクである。例として、低理解層、理解度ばらつき、誤概念、質問しにくさ、自己効力感の低さを抽出する。

## 判定基準

| criterion | 確認内容 |
| --- | --- |
| class_size_scalability | 3, 10, 20, 30人のクラスを同じ処理で扱えるか |
| score_distribution_visibility | 大きいクラスで低・中・高理解層が見えるか |
| trait_distribution_visibility | 個人特徴の複数レベルが見えるか |
| misconception_presence | 誤概念を持つ生徒が含まれるか |
| probe_response_distribution_visibility | 同じクラス内で代表問題への反応差が出るか |

## 論文での書き方

使える表現:

```text
複数生徒クラスの評価では、3人、10人、20人、30人のクラスを用意し、理解度分布、個人特徴分布、誤概念の有無、代表問題への予測正答率を比較した。これにより、生徒AIを個別エージェントとしてだけでなく、教師AIの授業設計入力となるクラス集団として扱えるかを確認した。
```

避ける表現:

```text
実際の30人学級を再現した。
現実のクラス分布と一致した。
実際の授業効果を予測できる。
```

## 限界

この評価は、実際の学校データとの比較ではない。したがって、外的妥当性はまだ主張しない。

この段階で主張できるのは、**複数生徒AIの内部状態分布を制御し、教師AIが利用できるクラス要約へ変換できる**という内部妥当性である。

## 次の段階

次は、伝達AIの推定妥当性を評価する。

確認すること:

1. 生徒の内部状態を隠す。
2. 発話、正誤、反応時間だけを伝達AIに渡す。
3. 伝達AIの推定結果と、隠された内部状態を比較する。
4. 完全一致ではなく、授業方針に使える粒度で一致しているかを見る。

