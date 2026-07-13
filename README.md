# Student AI MVP

一次方程式を学習する生徒AIのMVPです。Google Colabで実行することを前提に、GitHubからcloneしてそのまま動かせる構成にしています。

現在の主目的は、授業対話ではなく「生徒状態パラメータ、特に理解度スコアとテスト正答率の関係」を検証することです。LLMは「発話生成器」として使い、生徒の理解度・誤答傾向・性格・学習履歴は、LLM内部ではなく `data/students/*.json` で管理します。

## Colab前提のディレクトリ構造

```text
student-ai/
├─ README.md
├─ AGENTS.md
├─ requirements.txt
├─ notebooks/
│  ├─ student_ai_colab.ipynb
│  ├─ personality_experiment.ipynb
│  └─ teaching_strategy_experiment.ipynb
├─ src/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ model_loader.py
│  ├─ student_agent.py
│  ├─ student_ai.py
│  ├─ state_manager.py
│  ├─ logger.py
│  ├─ prompts.py
│  ├─ personality_model.py
│  ├─ observer/
│  │  ├─ __init__.py
│  │  ├─ observation_filter.py
│  │  ├─ observation_logger.py
│  │  └─ trait_classifier.py
│  ├─ teacher/
│  │  ├─ __init__.py
│  │  ├─ belief_manager.py
│  │  ├─ context_builder.py
│  │  ├─ intervention_planner.py
│  │  ├─ prompts.py
│  │  └─ strategy_selector.py
│  └─ cognitive_model.py
├─ data/
│  ├─ curriculum/
│  │  └─ linear_equation.json
│  ├─ observations/
│  │  └─ classroom_events.jsonl
│  ├─ students/
│  │  ├─ S001.json
│  │  ├─ S002.json
│  │  └─ S003.json
│  ├─ teacher_beliefs/
│  │  └─ T001/
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
- `notebooks/personality_experiment.ipynb`: 個人特徴による発話差を確認する実験ノートブック
- `notebooks/teaching_strategy_experiment.ipynb`: 生徒発話、伝達AIの観察、生徒状態から授業方略を決める実験ノートブック
- `src/config.py`: 既定モデルID、データパス、生成設定
- `src/model_loader.py`: Transformersモデル読み込み、4bit量子化設定
- `src/student_agent.py`: 生徒状態をもとにLLM発話を生成するエージェント
- `src/student_ai.py`: シミュレーターの実行入口
- `src/state_manager.py`: 生徒状態JSONの読み込み、検証、保存
- `src/logger.py`: `machine_readable.jsonl` と `human_readable.md` へのログ保存
- `src/prompts.py`: 一次方程式用プロンプト
- `src/personality_model.py`: 個人特徴を発話スタイル指示へ変換
- `src/observer/trait_classifier.py`: 伝達AI。生徒発話から個人特徴を分類し、1人または3〜20人のクラス全体要約を作る
- `src/observer/observation_filter.py`: 生徒AIの内部状態を隠し、授業中に観察できる情報だけをイベント化する
- `src/observer/observation_logger.py`: 授業中の観察イベントをJSONLに保存する
- `src/teacher/context_builder.py`: 教師AIが判断に使う生徒状態、単元目標、発話観察を1つのコンテキストにまとめる
- `src/teacher/belief_manager.py`: 観察イベントから教師側の生徒推定 `teacher_belief` を更新する
- `src/teacher/intervention_planner.py`: クラス全体対応と個別対応をルールベースで計画する
- `src/teacher/strategy_selector.py`: 教師AIの授業手法をルールベースで選ぶMVP
- `src/teacher/prompts.py`: 将来LLM教師に同じコンテキストを渡すためのプロンプト
- `data/curriculum/linear_equation.json`: 一次方程式の単元目標、スキル優先度、誤概念対応、次に出す問題
- `src/test_bank.py`: 学力テスト問題セットの読み込み
- `src/grader.py`: `x = 数値` 形式の採点
- `src/test_runner.py`: 生徒AIにテストを受けさせる実行器
- `src/cognitive_model.py`: テスト時に知識状態から正答/誤答方針を決める認知モデル
- `src/assessment_logger.py`: 学力テスト結果ログの保存
- `data/students/*.json`: 生徒ごとの状態データ
- `data/observations/`: 授業中に観察できたイベントログ
- `data/teacher_beliefs/`: 教師ごとに管理する生徒への推定状態
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
- 現在の検証フローでは授業による状態更新は実行しない
- 将来的に授業と生徒状態変化を扱えるよう、学習更新・誤概念解消の拡張点は残す
- ファインチューニングなし

## 内部状態と教師側推定の分離

生徒AIの真の内部状態は `data/students/*.json` に保存します。ただし、教師AIや伝達AIが授業中にこの真値を直接見る設計にはしません。

授業中に実環境で拾える情報だけを `observable_event` として作り、そこから教師側の推定値 `teacher_belief` を更新します。

```text
true student state
  ↓ 生徒AIの反応生成に使う。教師AIには直接見せない
observable_event
  ↓ 発話、回答、正誤、反応時間、質問有無、途中式有無など
teacher_belief
  ↓ 教師が日々の観察から徐々に持つ生徒理解
teacher AI context
```

`teacher_belief` は `data/teacher_beliefs/{teacher_id}/{student_id}.json` に保存します。初対面ではconfidenceが低く、観察が増えるほど推定のconfidenceが上がります。

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

- `knowledge_state`: 一次方程式に関する知識状態。知識スコアは0-100で扱う
- `misconceptions`: 誤概念
- `learning_speed`: 学習速度
- `big_five`: Big Five性格特性
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション
- `learning_history`: 学習履歴

互換用に `understanding`, `error_tendency`, `personality` も残しています。

### 知識状態 `knowledge_state`

一次方程式をどれくらい理解しているかを `0` から `100` のスコアで管理します。現在の検証ではテスト中に更新せず、初期パラメータとして正答率との関係を見ます。将来的には授業対話後に少しずつ更新する設計へ拡張できます。

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
| `misconceptions` | 生徒が持っている誤った考え方 | 誤答や迷いの原因として発話に反映される。テスト時は理解度が上がるほど影響が弱まる |
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

`src/personality_model.py` は、これらの個人特徴を発話スタイル指示へ変換します。

例:

```text
自信なさげに答える
具体的に質問する
途中式を丁寧に出す
不安や確認したい気持ちを出す
短めに答える
```

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

### 8. 現在の検証では授業対話は使わない

授業対話機能は将来拡張用に残していますが、現在の妥当性検証では使いません。中心に見るのは、`knowledge_state` と学力テスト正答率の関係です。

将来有効化する場合は、内部的には次のAPIを使います。

```python
result = sim.respond(STUDENT_ID, teacher_message)
```

### 9. 現在の検証では学習介入は使わない

講義後に状態変化を反映する設計は残していますが、現在の妥当性検証では使いません。将来的に授業後の状態変化を扱う場合は、次のAPIで知識スコアや誤概念解消を制御できます。

```python
learning_event = sim.apply_learning_intervention(
    STUDENT_ID,
    skill_deltas={
        "score": 15,
        "can_solve_ax_plus_b_equals_c": 15,
        "can_transpose_terms": 30,
        "can_divide_by_coefficient": 25,
        "can_handle_negative_numbers": 5,
        "can_handle_fractions": 0,
    },
    resolve_misconceptions=True,
)
```

### 10. LLMで学力テストを受けさせる

ノートブックの `Assessment test` セクションで、生徒AIにテストを受けさせられます。テストは授業中の発話ではなく、問題文に対する答えだけを出す形式です。テストは測定用なので、`knowledge_state` は更新しません。

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

### 11. パラメータによる誤答傾向を確認する

ノートブックの `Parameter error tendency check` セクションで、同じ問題を複数の検証用プロファイルに解かせ、回答と正誤を比較できます。

検証用プロファイル例:

- `PARAM_LOW_KNOWLEDGE`: 知識が低く、移項の誤概念が強い
- `PARAM_HIGH_ANXIETY`: 知識は中程度だが不安が強い
- `PARAM_HIGH_KNOWLEDGE`: 知識が高く、誤概念がほぼない

この検証では `update_knowledge=False` にしているため、知識スコアは更新されません。

### 12. 理解度と正答率の相関グラフを作る

ノートブックの `Understanding score vs accuracy graph` セクションで、理解度スコアと20問テストの正答率の相関を確認できます。

使うテスト:

```text
linear_equation_20q_001
```

検証内容:

- 理解度 `0,20,40,60,80,100` の検証用生徒を作る
- 20問テストを受けさせる
- 正答数と正答率を計算する
- 理解度スコアと正答率の散布図を描く
- 相関係数 `r` をグラフタイトルに表示する
- 問題ごとの正誤表を表示する
- 正誤表をCSV保存する

テスト時は `src/cognitive_model.py` が知識スコアから正答/誤答方針と `target_answer` を決めます。正答率の採点にはこの制御回答を使い、LLMの生出力は `raw_student_answer` として保存します。これにより、LLM本体の計算能力だけに引っ張られず、パラメータ差が正答率に出やすくなります。

同じ問題には全理解度で同じ判定ロールを使うため、理解度が上がるほど段階的に誤答が減りやすくなります。誤概念ペナルティは低理解度ほど強く、高理解度ほど弱くなり、90以上では同じ誤概念文が残っていてもテスト上の影響は無効になります。

この検証では `update_knowledge=False` なので、テスト中に知識スコアは更新されません。理解度スコアを変えた検証用生徒を複数作り、正答率の差を見る目的です。

保存されるCSV:

```text
data/assessments/understanding_accuracy_summary.csv
data/assessments/understanding_accuracy_detail.csv
data/assessments/understanding_accuracy_correctness_table.csv
```

### 13. 5刻み・大量問題で相関を見る

ノートブックの `Dense understanding sweep, 5-point intervals` セクションで、理解度 `0,5,10,...,100` の21段階をまとめて検証できます。

このセルはLLM発話を生成せず、`src/cognitive_model.py` だけで正答/誤答を決めます。そのため、Colabでも問題数を多めにできます。標準では500問です。

```python
UNDERSTANDING_SCORES_DENSE = list(range(0, 101, 5))
GENERATED_QUESTION_COUNT = 500
```

重い場合は `GENERATED_QUESTION_COUNT = 200` に下げます。余裕があれば `1000` 以上に増やせます。

保存されるCSV:

```text
data/assessments/dense_understanding_accuracy_summary.csv
data/assessments/dense_understanding_accuracy_detail.csv
data/assessments/dense_understanding_accuracy_correctness_table.csv
```

### 14. 授業ログを確認

```python
from pathlib import Path

print(Path("data/logs/human_readable.md").read_text(encoding="utf-8")[-2000:])
```

### 15. GitHubの更新をColabへ取り込む

ノートブック上部の `Pull latest code from GitHub` セルを実行します。clone直後に置いてあるので、基本的には上から順番に実行すれば最新版のコードを取り込めます。

```python
%cd /content/student-ai
!git status --short --branch
!git pull
```

その次の `Install dependencies` セルで依存関係をインストールします。依存関係が変わった場合も、上から順番に実行すれば反映されます。

```python
!pip install -q -r requirements.txt
```

注意: `student_ai_colab.ipynb` 自体のセル追加・移動は、すでに開いているColab画面には自動反映されないことがあります。その場合はGitHubから最新版のノートブックを開き直してください。

pullで衝突したり、Colab上の内容を捨ててGitHubの最新版で作り直す場合は、ノートブック下部の `Optional: reclone repository` セルを必要な場合だけ使います。

```python
%cd /content
!rm -rf student-ai
!git clone https://github.com/Hiromu-0219/student-ai-test.git /content/student-ai
%cd /content/student-ai
!pip install -q -r requirements.txt
```

## Colabノートブック

Colabでは [notebooks/student_ai_colab.ipynb](notebooks/student_ai_colab.ipynb) を使います。ノートブック冒頭でGitHub clone、GitHubからの更新取り込み、依存関係インストール、mock確認、4bit LLM実行まで順番に実行できます。

個人特徴による発話差を試す場合は [notebooks/personality_experiment.ipynb](notebooks/personality_experiment.ipynb) を使います。同じ知識状態で性格・心理パラメータだけを変え、発話から個人特徴を推定できるかを確認できます。

このノートブックでは標準で実LLMによる生徒発話を生成し、`src/observer/trait_classifier.py` の伝達AIも実行します。伝達AIは生徒発話を読み、プロファイル分類、特徴推定、先生AIに渡す要約、授業上の注意点を作ります。複数生徒を扱う場合は `summarize_classroom()` で3〜20人分の発話を集約し、クラス全体の傾向、優先対応が必要な生徒、教師への推奨行動を出します。

```text
data/assessments/communication_ai_trait_classification.csv
```

伝達AIも標準では実LLMで分類します。軽く確認したい場合は、`personality_experiment.ipynb` で次の値を `False` に変更します。

```python
USE_MOCK_MODEL = True
USE_LLM_COMMUNICATION_AI = False
```

このノートブックは、別AIに評価させるためのプロンプトも生成します。

```text
data/assessments/personality_judge_prompt.txt
```

この `.txt` の中身をChatGPTなどに貼ると、発話だけからプロファイル分類と特徴推定を行わせることができます。テンプレートは `data/prompts/personality_judge_prompt_template.txt` にあります。

授業手法を考える実験は [notebooks/teaching_strategy_experiment.ipynb](notebooks/teaching_strategy_experiment.ipynb) を使います。上から順番に実行すると、GitHubから最新版を取り込み、生徒AIの発話を作り、伝達AIで個別観察とクラス全体要約を行い、`src/teacher/` のルールベース教師が次の授業方略を選びます。

このノートブックでは `S001`, `S002`, `S003` の3人を実際に同じ教師発話へ反応させ、観察イベントから教師側推定 `teacher_belief` を更新します。更新後は、推定理解度、confidence、自己効力感、質問傾向、モチベーション、不安傾向を表で確認できます。

```text
data/assessments/observable_events_latest.json
data/assessments/teacher_beliefs_latest.json
data/assessments/teacher_belief_table_latest.csv
```

さらに、L001〜L003の3回分の授業を連続実行し、`teacher_belief` が蓄積されるかを検証できます。推定理解度とconfidenceの推移は表とグラフで確認でき、次のCSVにも保存されます。

```text
data/assessments/teacher_belief_progress_validation.csv
data/assessments/observable_events_validation.json
```

その後、`src/teacher/intervention_planner.py` により、クラス全体への授業行動と個別支援を分けて計画します。現在はLLMを使わず、クラス要約、教師側belief、直近の正誤から判断します。

```text
data/assessments/intervention_plan_latest.json
```

この段階では、教師AIの判断はLLMに任せず、まず判断理由を追跡しやすいルールで実装しています。将来的にLLM教師へ置き換える場合は、`src/teacher/prompts.py` のプロンプトに `teacher_context` を渡します。

## テスト

標準テストではモデルをダウンロードしません。`use_mock_model=True` で実行経路を確認します。

```bash
python -m pytest
```
