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
│  ├─ prompts.py
│  └─ cognitive_model.py
├─ data/
│  ├─ students/
│  │  ├─ S001.json
│  │  ├─ S002.json
│  │  └─ S003.json
│  ├─ logs/
│  │  ├─ machine_readable.jsonl
│  │  └─ human_readable.md
│  ├─ tests/
│  │  ├─ linear_equation_basic_001.json
│  │  └─ linear_equation_20q_001.json
│  └─ assessments/
│     ├─ machine_readable.jsonl
│     └─ human_readable.md
└─ tests/
   ├─ test_state_manager.py
   ├─ test_logger.py
   ├─ test_student_ai.py
   ├─ test_grader.py
   └─ test_test_runner.py
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
- `src/test_bank.py`: 学力テスト問題セットの読み込み
- `src/grader.py`: `x = 数値` 形式の採点
- `src/test_runner.py`: 生徒AIにテストを受けさせる実行器
- `src/cognitive_model.py`: テスト時に知識状態から正答/誤答方針を決める認知モデル
- `src/assessment_logger.py`: 学力テスト結果ログの保存
- `data/students/*.json`: 生徒ごとの状態データ
- `data/logs/`: 回答ログの保存先
- `data/tests/`: 学力テスト問題セット
- `data/assessments/`: 学力テスト結果ログの保存先
- `tests/`: mock modelを使う最小テスト

## 実装範囲

- 一次方程式のみ対応
- 生徒状態はJSONで管理
- 生徒状態には知識状態、誤概念、学習速度、Big Five、自己効力感、質問傾向、モチベーションを持たせる
- LLMは発話生成器として利用
- TransformersでローカルLLMを読み込み
- bitsandbytesによる4bit量子化に対応
- 回答ログをJSONLとMarkdownに保存
- 学力テストを受けさせ、得点とスキル別正答率を保存
- ファインチューニングなし

## 想定モデル

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

`Qwen/Qwen3-4B` は `transformers>=4.51.0` が必要です。Gemma系の gated model を使う場合は、Hugging Face login が必要になることがあります。

## 生徒状態パラメータ

`data/students/*.json` には主に次のパラメータを持たせます。

性格・心理系の段階値は原則として次の5段階で扱います。

```text
very_low / low / medium / high / very_high
```

- `knowledge_state`: 一次方程式に関する知識状態。知識スコアは0-100で扱い、授業対話により少しずつ更新する
- `misconceptions`: 誤概念
- `learning_speed`: 学習速度
- `big_five`: Big Five性格特性
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション
- `learning_history`: 学習履歴

互換用に `understanding`, `error_tendency`, `personality` も残しています。

### 知識状態 `knowledge_state`

一次方程式をどれくらい理解しているかを `0` から `100` のスコアで管理します。授業対話後に少しずつ更新されます。

| パラメータ | 意味 | 低い場合 | 高い場合 |
| --- | --- | --- | --- |
| `score` | 一次方程式全体の総合理解度 | 解き方の方針が立たない | 自力で解ける |
| `can_solve_ax_plus_b_equals_c` | `ax + b = c` 型を解く力 | 何から始めるか迷う | 標準問題を解ける |
| `can_transpose_terms` | 移項の理解 | 符号を変え忘れる | 移項を安定して使える |
| `can_divide_by_coefficient` | 係数で割る理解 | `3x = 15` で3を引くなどの誤り | 係数で割って `x` を求められる |
| `can_handle_negative_numbers` | 負の数を含む式への対応 | マイナスで混乱する | 符号を正しく扱える |
| `can_handle_fractions` | 分数を含む式への対応 | 分数係数で止まる | 分数でも整理できる |

`level` は `score` から自動的に更新される表示用ラベルです。

| score範囲 | level |
| --- | --- |
| `0-19` | `very_low` |
| `20-39` | `low` |
| `40-59` | `medium` |
| `60-79` | `high` |
| `80-100` | `very_high` |

### 誤概念・学習特性

| パラメータ | 意味 | 反応への影響 |
| --- | --- | --- |
| `misconceptions` | 生徒が持っている誤った考え方 | 誤答や迷いの原因として発話に反映される |
| `learning_speed` | 授業による知識スコアの伸びやすさ | 高いほど1回の対話で知識スコアが上がりやすい |
| `learning_history` | 過去の教師発話、生徒回答、知識更新記録 | 直近履歴がプロンプトに入り、継続授業らしさが出る |

### 心理・性格パラメータ

心理・性格系は5段階です。

| パラメータ | 意味 | 低い場合 | 高い場合 |
| --- | --- | --- | --- |
| `self_efficacy` | 自己効力感。「自分は解ける」と思える度合い | 自信なさげ、確認が多い | 自信を持って答える |
| `question_tendency` | 質問傾向 | わからなくても黙りやすい | つまずきを質問しやすい |
| `motivation` | 学習意欲 | 粘りにくい、短い返答 | 前向きに取り組む |
| `big_five.openness` | 開放性。新しい解き方への受け入れやすさ | 慣れた手順に固執 | 別解や説明を受け入れやすい |
| `big_five.conscientiousness` | 誠実性。丁寧さ、手順を守る傾向 | 途中式を飛ばす | 丁寧に式を書く |
| `big_five.extraversion` | 外向性。発話量や反応の積極性 | 返答が短い | よく話す |
| `big_five.agreeableness` | 協調性。教師への合わせやすさ | そっけない | 素直に反応する |
| `big_five.neuroticism` | 神経症傾向。不安や焦りやすさ | 落ち着いている | 不安、迷いが出やすい |

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

- `MODEL_ID`: 使用するHugging FaceモデルID。例: `Qwen/Qwen3-4B`
- `max_new_tokens`: 回答の最大長。短い生徒回答なら `128` から `256`
- `temperature`: 高いほど揺れが大きい。安定させるなら `0.3` から `0.7`
- `top_p`: 低いほど候補を絞る。通常は `0.8` から `0.95`
- `do_sample`: `True` なら毎回少し揺れる。`False` なら安定寄り
- `repetition_penalty`: 繰り返し抑制。通常は `1.0` から `1.15`
- `load_in_4bit`: Colab GPUでメモリを節約するなら `True`
- `bnb_4bit_quant_type`: 4bit量子化方式。通常は `nf4`
- `bnb_4bit_use_double_quant`: さらにメモリを節約する設定。通常は `True`
- `compute_dtype`: 計算精度。Colabではまず `bfloat16`、動かない場合は `float16`

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

知識状態は100段階スコアです。

```json
"knowledge_state": {
  "linear_equation": {
    "level": "low",
    "score": 25,
    "can_solve_ax_plus_b_equals_c": 25,
    "can_transpose_terms": 5,
    "can_divide_by_coefficient": 20,
    "can_handle_negative_numbers": 5,
    "can_handle_fractions": 5
  }
}
```

`score` と各スキルは `0` から `100` で、`level` はスコアから `very_low / low / medium / high / very_high` に更新されます。

性格・心理系の5段階値:

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

### 9. LLMで学力テストを受けさせる

ノートブックの `Assessment test` セクションで、生徒AIにテストを受けさせられます。`Create simulator` セクションで `USE_MOCK_MODEL=False` にしていれば、QwenなどのLLMが生徒として解答します。テストは測定用なので、`knowledge_state` は更新しません。

```python
USE_MOCK_MODEL = False  # LLMで受験させる
```

```python
from src.test_runner import TestRunner

TEST_ID = "linear_equation_basic_001"

runner = TestRunner(simulator=sim)
assessment_result = runner.run_test(
    student_id=STUDENT_ID,
    test_id=TEST_ID,
)

print("テスト:", assessment_result["title"])
print("得点:", assessment_result["score_percentage"], "%")
print("正答数:", assessment_result["correct_count"], "/", assessment_result["total_count"])
print("スキル別スコア:")
for skill, score in assessment_result["skill_scores"].items():
    print("-", skill, score, "%")
```

評価ログはここに保存されます。

```python
from pathlib import Path

print(Path("data/assessments/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

### 10. パラメータによる誤答傾向を確認する

ノートブックの `Parameter error tendency check` セクションで、同じ問題を複数の検証用プロファイルに解かせ、回答と正誤を比較できます。

検証用プロファイル例:

- `PARAM_LOW_KNOWLEDGE`: 知識が低く、移項の誤概念が強い
- `PARAM_HIGH_ANXIETY`: 知識は中程度だが不安が強い
- `PARAM_HIGH_KNOWLEDGE`: 知識が高く、誤概念がほぼない

この検証では `update_knowledge=False` にしているため、知識スコアは更新されません。

### 11. 理解度と正答率の相関グラフを作る

ノートブックの `Understanding score vs accuracy graph` セクションで、理解度スコアと20問テストの正答率の相関を確認できます。

使うテスト:

```text
linear_equation_20q_001
```

検証内容:

- 理解度 `0,20,40,60,80,100` の検証用生徒を作る
- 20問テストを受けさせる
- 正答率を計算する
- 理解度スコアと正答率の散布図を描く
- 相関係数 `r` をグラフタイトルに表示する

テスト時は `src/cognitive_model.py` が知識スコアから正答/誤答方針を決め、その方針をLLMに渡します。これにより、LLM本体の計算能力だけに引っ張られず、パラメータ差が正答率に出やすくなります。

この検証でも `update_knowledge=False` なので、テスト中に知識スコアは更新されません。講義前に実行し、`Interactive lesson` で授業をした後にもう一度実行すると、授業前後の正答率変化を比較できます。

### 12. 授業ログを確認

```python
from pathlib import Path

print(Path("data/logs/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

### 13. GitHubの更新をColabへ取り込む

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
