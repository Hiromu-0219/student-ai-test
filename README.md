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
- 生徒状態には知識状態、誤概念、学習速度、Big Five、自己効力感、質問傾向、モチベーションを持たせる
- LLMは発話生成器として利用
- TransformersでローカルLLMを読み込み
- bitsandbytesによる4bit量子化に対応
- 回答ログをJSONLとMarkdownに保存
- ファインチューニングなし

## 想定モデル

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

`Qwen/Qwen3-4B` は `transformers>=4.51.0` が必要です。Gemma系の gated model を使う場合は、Hugging Face login が必要になることがあります。

## 生徒状態パラメータ

`data/students/*.json` には主に次のパラメータを持たせます。

段階値は原則として次の5段階で扱います。

```text
very_low / low / medium / high / very_high
```

- `knowledge_state`: 一次方程式に関する知識状態
- `misconceptions`: 誤概念
- `learning_speed`: 学習速度
- `big_five`: Big Five性格特性
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション
- `learning_history`: 学習履歴

互換用に `understanding`, `error_tendency`, `personality` も残しています。

## ColabでGitHubから動かす手順

### 1. GPUランタイムを選ぶ

Colabで `ランタイム > ランタイムのタイプを変更 > GPU` を選択します。

### 2. GitHubからcloneする

`REPO_URL` は設定済みです。

```python
REPO_URL = "https://github.com/Hiromu-0219/student-ai-test.git"

!git clone {REPO_URL} /content/student-ai
%cd /content/student-ai
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

生成パラメータは必要に応じて調整できます。

```python
from src.config import GenerationConfig, ModelLoadConfig
from src.student_ai import StudentAISimulator

model_load_config = ModelLoadConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    compute_dtype="bfloat16",
)

generation_config = GenerationConfig(
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
    repetition_penalty=1.05,
)

sim = StudentAISimulator(
    model_id="Qwen/Qwen3-4B",
    load_in_4bit=model_load_config.load_in_4bit,
    model_load_config=model_load_config,
    generation_config=generation_config,
)

result = sim.answer(
    student_id="S001",
    problem="2x + 3 = 11 を解いてください。",
)

print(result["answer"])
```

パラメータの目安:

- `max_new_tokens`: 回答の最大長。短い生徒回答なら `128` から `256`
- `temperature`: 高いほど揺れが大きい。安定させるなら `0.3` から `0.7`
- `top_p`: 低いほど候補を絞る。通常は `0.8` から `0.95`
- `repetition_penalty`: 繰り返し抑制。通常は `1.0` から `1.15`
- `load_in_4bit`: Colab GPUでメモリを節約するなら `True`

### 7. 生徒パラメータを編集する

ノートブックの `Student parameters` セクションで、授業に使う生徒IDと状態を変更できます。

```python
STUDENT_ID = "S002"

student_state["learning_speed"] = "low"
student_state["self_efficacy"] = "low"
student_state["question_tendency"] = "high"
student_state["motivation"] = "medium"
```

主に編集する項目:

- `knowledge_state`: 知識状態
- `misconceptions`: 誤概念
- `learning_speed`: 学習速度
- `big_five`: Big Five
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション

5段階値:

```text
very_low / low / medium / high / very_high
```

### 8. 対話授業をする

ノートブックの `Interactive lesson` セクションを実行すると、教師として発話を入力できます。

```python
while True:
    teacher_message = input("教師> ").strip()
    if teacher_message.lower() in {"exit", "quit", "終了"}:
        break

    result = sim.respond(STUDENT_ID, teacher_message)
    print("生徒AI>", result["answer"])
```

例:

```text
教師> 今日は 2x + 3 = 11 を一緒に解こう。まず何をすればいい？
生徒AI> えっと、3を右に動かすと思います。でも符号を変えるんでしたっけ？
```

### 9. ログを確認

```python
from pathlib import Path

print(Path("data/logs/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

### 10. GitHubの更新をColabへ取り込む

GitHub側のコードを更新したあと、Colabでは次を実行します。

```python
%cd /content/student-ai
!git status
!git pull
```

依存関係が変わった場合は、pull後に再インストールします。

```python
!pip install -q -r requirements.txt
```

pullで衝突したり、Colab上の内容を捨ててGitHubの最新版で作り直す場合は、cloneし直します。

```python
%cd /content
!rm -rf student-ai
!git clone https://github.com/Hiromu-0219/student-ai-test.git /content/student-ai
%cd /content/student-ai
!pip install -q -r requirements.txt
```

## Colabノートブック

Colabでは [notebooks/student_ai_colab.ipynb](notebooks/student_ai_colab.ipynb) を使います。ノートブック冒頭でGitHub clone、依存関係インストール、mock確認、4bit LLM実行、GitHubからの更新取り込みまで順番に実行できます。

## テスト

標準テストではモデルをダウンロードしません。`use_mock_model=True` で実行経路を確認します。

```bash
python -m pytest
```
