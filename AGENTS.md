# AGENTS.md

## Project Goal

一次方程式を学習する生徒AIのMVPを作る。

このプロジェクトでは、LLMを「発話生成器」として使う。生徒の理解度、誤答傾向、性格、学習履歴はLLM内部ではなく、`data/students/*.json` で管理する。

## Runtime

- Google Colab で動くことを優先する。
- ColabではGitHubから `student-ai` をcloneし、repo rootで実行する前提にする。
- Colab実行例は `notebooks/student_ai_colab.ipynb` に置く。
- ローカルLLMは `transformers` で読み込む。
- 4bit量子化は `bitsandbytes` の `BitsAndBytesConfig` を使う。
- 最初はファインチューニングしない。

## Model Candidates

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

Gemma系の gated model を使う場合は、Colab上で Hugging Face login が必要になることがある。

## Data Model

生徒状態は `data/students/{student_id}.json` に保存する。

知識状態は `knowledge_state.linear_equation.score` と各スキルを0-100の整数スコアで扱う。授業対話後に少しずつ更新する。

性格・心理系の段階評価は原則として `very_low`, `low`, `medium`, `high`, `very_high` の5段階で扱う。

必須フィールド:

- `understanding`
- `knowledge_state`
- `error_tendency`
- `misconceptions`
- `learning_speed`
- `personality`
- `big_five`
- `self_efficacy`
- `question_tendency`
- `motivation`
- `learning_history`

## Logging

回答ログは2種類保存する。

- `data/logs/machine_readable.jsonl`
- `data/logs/human_readable.md`

学力テスト結果ログは2種類保存する。

- `data/assessments/machine_readable.jsonl`
- `data/assessments/human_readable.md`

## Current Scope

- 対応科目: 数学
- 対応単元: 一次方程式
- 対応動作: 教師が問題文を入力し、生徒AIが状態に基づいて回答する
- 学力テストは測定用として扱い、標準では `knowledge_state` を更新しない

## Testing

モデルのダウンロードを伴うテストは標準テストに含めない。通常のテストでは `use_mock_model=True` を使い、状態管理、ログ保存、実行経路を確認する。

```bash
python -m pytest
```
