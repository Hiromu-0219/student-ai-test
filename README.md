# Student AI Education Simulation

一次方程式を学習する生徒AIと、複数生徒クラスを観察して授業方略を考える教育シミュレーションのMVPです。

このプロジェクトでは、LLMを主に「発話生成器」として使います。生徒の理解度、誤概念、個人特徴、学習履歴はLLM内部ではなく、`data/students/*.json` で管理します。

## 研究上のコア

現在の中心テーマは、次の流れが教育シミュレーションとして成立するかを検証することです。

```text
真の生徒状態
  ↓ 生徒AIの授業中反応
観察可能な発話・回答・正誤
  ↓ 伝達AIによる個人特徴推定とクラス要約
教師AIが持つ生徒理解 teacher_belief
  ↓
授業構成・個別支援・教師発話の生成
```

教師AIや伝達AIは、生徒の内部JSONを直接見る前提にはしません。授業中に観察できる情報から、徐々に生徒理解を更新する設計です。

## ディレクトリ構造

```text
student-ai/
  notebooks/
    README.md
    paper_core_experiment.ipynb
    student_ai_colab.ipynb
    personality_experiment.ipynb
    teaching_strategy_experiment.ipynb
  src/
    experiment/
      experiment_config.py
      teaching_strategy_runner.py
      result_exporter.py
    observer/
      observation_filter.py
      observation_logger.py
      trait_classifier.py
    teacher/
      belief_manager.py
      context_builder.py
      intervention_planner.py
      lesson_planner.py
      lesson_session_runner.py
      strategy_selector.py
      utterance_builder.py
    class_manager.py
    cognitive_model.py
    model_loader.py
    personality_model.py
    prompts.py
    student_ai.py
    student_agent.py
    state_manager.py
  data/
    classes/
    curriculum/
    students/
    teacher_beliefs/
    logs/
    assessments/
  tests/
  docs/
```

## Notebookの役割

| Notebook | 目的 |
| --- | --- |
| `paper_core_experiment.ipynb` | 論文用の最小実験、使用ソースコード、確認観点を整理 |
| `student_ai_colab.ipynb` | 生徒AIの設計確認、理解度と正答率の学習曲線確認 |
| `personality_experiment.ipynb` | 個人特徴が発話に反映され、伝達AIが分類できるか確認 |
| `teaching_strategy_experiment.ipynb` | 複数生徒クラス、伝達AI要約、教師AIの授業方略を確認 |

詳細は `notebooks/README.md` にまとめています。

## Colabでの実行手順

1. ColabでGPUランタイムを選びます。

```text
ランタイム > ランタイムのタイプを変更 > GPU
```

2. GitHubからcloneします。

```python
REPO_URL = "https://github.com/Hiromu-0219/student-ai-test.git"

!git clone {REPO_URL} /content/student-ai
%cd /content/student-ai
```

3. 依存関係をインストールします。

```python
!pip install -q -r requirements.txt
```

4. Notebookを上から実行します。

まず軽く確認する場合は、`student_ai_colab.ipynb` のmock model確認から実行してください。
授業方略のメイン実験は `teaching_strategy_experiment.ipynb` を使います。

## ColabでGitHub更新を反映する

Colab上のrepoを更新する場合は、次を実行します。

```python
%cd /content/student-ai
!git fetch origin main
!git reset --hard origin/main
!git log -1 --oneline
```

注意: Git更新セルを実行しても、すでに開いているColab Notebook画面のセル内容は自動では書き換わらないことがあります。Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。

## LLM設定

ローカルLLMは `transformers` で読み込みます。4bit量子化には `bitsandbytes` を使います。

想定モデル:

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

Colabで軽く試す場合は、より小さいモデルを使うか、まず `use_mock_model=True` で動作確認してください。Gemma系のgated modelを使う場合は、Hugging Face loginが必要になることがあります。

## 生徒状態

生徒状態は `data/students/{student_id}.json` に保存します。

主なフィールド:

- `knowledge_state`: 一次方程式の理解度。スコアは0-100
- `misconceptions`: 誤概念
- `error_tendency`: 誤答傾向
- `learning_speed`: 学習速度
- `big_five`: Big Five特性
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション
- `learning_history`: 学習履歴

性格・心理系の段階評価は原則として `very_low`, `low`, `medium`, `high`, `very_high` の5段階です。

## 内部構造

主要な責務は次のように分けています。

- `src/student_ai.py`: 生徒AIシミュレータの入口
- `src/prompts.py`: 生徒AI用プロンプト
- `src/cognitive_model.py`: 理解度に基づく正答・誤答制御
- `src/personality_model.py`: 個人特徴を発話スタイルへ変換
- `src/observer/`: 伝達AI。観察可能な発話から特徴推定・クラス要約を行う
- `src/teacher/`: 教師AI。teacher_belief、授業計画、個別支援、教師発話を扱う
- `src/experiment/`: Notebookから呼び出す実験実行・結果保存の入口

メイン実験は次のように呼び出せます。

```python
from src.experiment import TeachingStrategyExperimentConfig, run_teaching_strategy_experiment

result = run_teaching_strategy_experiment(
    TeachingStrategyExperimentConfig(
        class_id="class_3_basic",
        use_mock_student=True,
    )
)

print(result["summary"])
```

## テスト

通常テストではモデルのダウンロードを行いません。mock modelを使って、状態管理、ログ保存、伝達AI、教師AI、実験ランナーの経路を確認します。

```bash
python -m pytest
```

## 現在のスコープ

- 対応科目: 数学
- 対応単元: 一次方程式
- 対応人数: 3-20人程度のクラス
- ファインチューニング: なし
- 主な検証:
  - 理解度と正答率の関係
  - 個人特徴が発話に反映されるか
  - 伝達AIが複数生徒の反応を要約できるか
  - 教師AIが要約に基づいて授業構成・個別支援を変えられるか
