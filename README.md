# Student AI MVP

一次方程式を学習する生徒AIのMVPです。

LLMは「発話生成器」として使い、生徒の理解度・誤答傾向・性格・学習履歴は `data/students/*.json` で管理します。最初はファインチューニングせず、TransformersでローカルLLMを読み込みます。

## 作成するファイルと役割

```text
student-ai/
├─ README.md
├─ AGENTS.md
├─ requirements.txt
├─ notebooks/
│  └─ student_ai_colab.ipynb
├─ src/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ model_loader.py
│  ├─ student_agent.py
│  ├─ student_ai.py
│  ├─ state_manager.py
│  ├─ logger.py
│  └─ prompts.py
├─ data/
│  ├─ students/
│  │  ├─ S001.json
│  │  ├─ S002.json
│  │  └─ S003.json
│  └─ logs/
│     ├─ machine_readable.jsonl
│     └─ human_readable.md
└─ tests/
   ├─ test_state_manager.py
   ├─ test_logger.py
   └─ test_student_ai.py
```

- `README.md`: プロジェクト概要とColabでの実行手順
- `AGENTS.md`: 開発・運用方針
- `requirements.txt`: Colab/ローカル実行に必要なPython依存関係
- `notebooks/student_ai_colab.ipynb`: Colab実行用ノートブック
- `src/config.py`: 既定モデルID、データパス、生成設定
- `src/model_loader.py`: Transformersモデル読み込みと4bit量子化
- `src/student_agent.py`: 生徒状態に基づく発話生成エージェント
- `src/student_ai.py`: シミュレーターの実行入口
- `src/state_manager.py`: 生徒状態JSONの読み書きと検証
- `src/logger.py`: JSONLとMarkdownのログ保存
- `src/prompts.py`: 一次方程式用プロンプト
- `data/students/*.json`: サンプル生徒状態
- `data/logs/`: 回答ログの保存先
- `tests/`: 状態管理、ログ、シミュレーター経路の最小テスト

## 実装範囲

- 一次方程式のみ対応
- 生徒状態はJSONで管理
- LLMは回答文の生成だけに使う
- TransformersでローカルLLMを読み込み
- bitsandbytesによる4bit量子化に対応
- 回答ログを `machine_readable.jsonl` と `human_readable.md` に保存
- ファインチューニングなし

## Model Candidates

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

`Qwen/Qwen3-4B` は `transformers>=4.51.0` が必要です。Gemma系の gated model を使う場合は Hugging Face login が必要になることがあります。

## Colabでの実行手順

### 1. GPUランタイムを選ぶ

Colabのメニューで `ランタイム > ランタイムのタイプを変更 > GPU` を選択します。

### 2. 依存関係をインストール

```python
!pip install -q -r requirements.txt
```

### 3. 必要に応じてHugging Faceへログイン

```python
from huggingface_hub import login
login()
```

### 4. まずmock modelで疎通確認

```python
from src.student_ai import StudentAISimulator

sim = StudentAISimulator(use_mock_model=True)

result = sim.answer(
    student_id="S001",
    problem="2x + 3 = 11 を解いてください。",
)

print(result["answer"])
```

### 5. Qwen3 4Bを4bitで実行

```python
from src.student_ai import StudentAISimulator

sim = StudentAISimulator(
    model_id="Qwen/Qwen3-4B",
    load_in_4bit=True,
)

result = sim.answer(
    student_id="S001",
    problem="2x + 3 = 11 を解いてください。",
)

print(result["answer"])
```

### 6. ログ確認

```python
from pathlib import Path

print(Path("data/logs/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

## テスト

モデルのダウンロードを伴うテストは標準テストに含めていません。通常テストでは mock model を使います。

```bash
python -m pytest
```
