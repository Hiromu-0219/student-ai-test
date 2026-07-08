# Student AI MVP

一次方程式を学習する生徒AIのMVPです。Google Colabで実行することを前提に、GitHubからcloneしてそのまま動かせる構成にしています。

LLMは「発話生成器」としてのみ使います。生徒の理解度・誤答傾向・性格・学習履歴は、LLM内部ではなく `data/students/*.json` で管理します。

## Colab前提のディレクトリ構造

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

## 各ファイルの役割

- `README.md`: プロジェクト概要、ディレクトリ構造、Colab実行手順
- `AGENTS.md`: 開発・運用方針
- `requirements.txt`: Colabでインストールする依存関係
- `notebooks/student_ai_colab.ipynb`: Colab実行用ノートブック
- `src/config.py`: 既定モデルID、データパス、生成設定
- `src/model_loader.py`: Transformersモデル読み込み、4bit量子化設定
- `src/student_agent.py`: 生徒状態をもとにLLM発話を生成するエージェント
- `src/student_ai.py`: シミュレーターの実行入口
- `src/state_manager.py`: 生徒状態JSONの読み込み、検証、保存
- `src/logger.py`: `machine_readable.jsonl` と `human_readable.md` へのログ保存
- `src/prompts.py`: 一次方程式用プロンプト
- `data/students/*.json`: 生徒ごとの状態データ
- `data/logs/`: 回答ログの保存先
- `tests/`: mock modelを使う最小テスト

## 実装範囲

- 一次方程式のみ対応
- 生徒状態はJSONで管理
- LLMは発話生成器として利用
- TransformersでローカルLLMを読み込み
- bitsandbytesによる4bit量子化に対応
- 回答ログをJSONLとMarkdownに保存
- ファインチューニングなし

## 想定モデル

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

`Qwen/Qwen3-4B` は `transformers>=4.51.0` が必要です。Gemma系の gated model を使う場合は、Hugging Face login が必要になることがあります。

## ColabでGitHubから動かす手順

### 1. GPUランタイムを選ぶ

Colabで `ランタイム > ランタイムのタイプを変更 > GPU` を選択します。

### 2. GitHubからcloneする

`REPO_URL` は自分のGitHubリポジトリURLに置き換えてください。

```python
REPO_URL = "https://github.com/YOUR_NAME/student-ai.git"

!git clone {REPO_URL}
%cd student-ai
```

すでにColab上にclone済みの場合は、次のように移動します。

```python
%cd /content/student-ai
```

### 3. 依存関係をインストール

```python
!pip install -q -r requirements.txt
```

### 4. 必要に応じてHugging Faceへログイン

Gemma系モデルやprivate/gated modelを使う場合に実行します。

```python
from huggingface_hub import login
login()
```

### 5. mock modelで疎通確認

まずモデルをダウンロードせず、状態管理・回答生成・ログ保存の経路だけ確認します。

```python
from src.student_ai import StudentAISimulator

sim = StudentAISimulator(use_mock_model=True)

result = sim.answer(
    student_id="S001",
    problem="2x + 3 = 11 を解いてください。",
)

print(result["answer"])
```

### 6. Qwen3 4Bを4bitで実行

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

### 7. ログを確認

```python
from pathlib import Path

print(Path("data/logs/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

## Colabノートブック

Colabでは [notebooks/student_ai_colab.ipynb](notebooks/student_ai_colab.ipynb) を使います。ノートブック冒頭でGitHub clone、依存関係インストール、mock確認、4bit LLM実行まで順番に実行できます。

## テスト

標準テストではモデルをダウンロードしません。`use_mock_model=True` で実行経路を確認します。

```bash
python -m pytest
```
