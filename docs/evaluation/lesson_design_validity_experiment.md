# 授業設計AIの妥当性実験

最終更新: 2026-08-07 15:51:27 JST

## 目的

第4段階では、授業設計AIが伝達AIから教師側に渡された推定情報をもとに、クラス全体に合った講義構成を提案できるかを検証する。

この段階で確認するのは、個々の生徒を正確に診断することではなく、クラス全体の状態を見て授業の方針を変えられるかである。

## シミュレーション上の位置づけ

```text
生徒AI
  -> 観察可能な発話・正誤・反応を出す
伝達AI
  -> 観察可能情報から teacher_beliefs を作る
授業設計AI
  -> teacher_beliefs と curriculum から講義全体を設計する
教師発話AI
  -> 授業設計に沿って発話する
```

授業設計AIは、生徒の真の内部状態を直接見ない。入力は `teacher_beliefs` と `curriculum` である。

## 比較するクラス条件

### low_understanding_class

低理解の生徒が多いクラス。全体説明と例題を厚めにし、基本操作に戻る設計になるかを見る。

### wide_gap_class

低理解から高理解まで幅があるクラス。全体説明だけで進めず、個別演習と対象別支援を厚めにするかを見る。

### high_understanding_class

理解度が高めのクラス。標準ペースで進め、確認・演習に移れるかを見る。

### common_misconception_class

共通誤概念があるクラス。平均理解度だけでなく、誤概念に応じた授業目標が選ばれるかを見る。

## 評価指標

### observable_input_policy

授業設計AIが `teacher_beliefs` 由来の推定情報だけを使い、真の内部状態を使わない設計になっているかを見る。

### goal_adaptation

クラス条件に応じて授業目標が変わるかを見る。

例:

- 低理解クラス: `can_transpose_terms`
- 高理解クラス: `can_divide_by_coefficient`
- 共通誤概念クラス: `can_divide_by_coefficient`

### time_allocation_adaptation

クラス条件に応じて時間配分が変わるかを見る。

- 低理解クラス: 全体説明を厚くする
- 学力差クラス: 個別演習を厚くする
- 高理解クラス: 標準ペースで進める

### whole_class_optimization_targets

授業設計AIが、クラス全体のリスクに応じて最適化対象を出せるかを見る。

例:

- 低理解層支援
- 生徒間ギャップ縮小
- 共通誤概念への対応
- 教師主導の確認質問

### individual_support_policy_presence

講義全体の設計だけでなく、個別演習中にどの生徒へどのように支援するかも出せるかを見る。

## 実行方法

```bash
python scripts/run_lesson_design_validity_experiment.py
```

出力:

```text
data/assessments/lesson_design_validity_for_codex.txt
```

## 主張範囲

この実験で主張できるのは、授業設計AIが観察由来のクラス要約に反応して講義構成を変えられることである。

実際の授業効果が上がること、人間教師より優れていること、現実の教室を完全に再現できることは、この実験だけでは主張しない。


