# Student AI Education Simulation

一次方程式を学習する生徒AIと、複数生徒クラスを観察して授業方針を考える教育シミュレーションのMVPです。

このプロジェクトでは、LLMを主に「発話生成器」として使います。生徒の理解度、誤概念、個人特徴、学習履歴はLLM内部ではなく、`data/students/*.json` で管理します。

## 研究のコア

現在の研究上の中心は、AI生徒を人間の完全な代替として使うことではありません。

主張する範囲は次です。

> 一次方程式の学習場面において、理解度・誤概念・個人特徴を外部状態として制御した生徒AIが、教師AIの授業設計を検証するための「限定的な学習者代理」として利用可能かを検証する。

見るべきポイント:

- 理解度が上がると正答率が上がるか
- 誤概念があると関連問題で誤答しやすくなるか
- 理解度が上がると誤概念の影響が弱まるか
- 弱点スキルを変えると結果が変わるか
- 自己効力感、質問傾向、意欲、Big Five が発話に反映されるか
- 教師AI・伝達AIが内部状態ではなく、授業中に観察できる情報だけを使って判断できるか

生徒AIそのものの設計は [docs/student_ai_design.md](docs/student_ai_design.md) を見てください。内部妥当性の評価手順は [docs/internal_validity_experiment.md](docs/internal_validity_experiment.md)、論文用の実験設計は [docs/paper_experiment_core.md](docs/paper_experiment_core.md) に整理しています。設計要素と参考文献の対応は [docs/reference_mapping.md](docs/reference_mapping.md) にまとめています。

## ディレクトリ構成

```text
student-ai/
  notebooks/
    paper_core_experiment.ipynb
    student_ai_colab.ipynb
    personality_experiment.ipynb
    teaching_strategy_experiment.ipynb
  src/
    experiment/
    observer/
    teacher/
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
    tests/
    logs/
    assessments/
  docs/
  tests/
```

## Notebookの役割

| Notebook | 役割 |
| --- | --- |
| `notebooks/student_ai_colab.ipynb` | 生徒AI単体の設計確認、学習曲線、誤概念、個人特徴の評価 |
| `notebooks/personality_experiment.ipynb` | 個人特徴が発話に出るか、伝達AIが分類できるかの確認 |
| `notebooks/teaching_strategy_experiment.ipynb` | 複数生徒クラス、伝達AI要約、教師AIの授業方針生成の確認 |
| `notebooks/paper_core_experiment.ipynb` | 論文用に使う最小実験と出力確認 |

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

3. 依存関係を入れます。

```python
!pip install -q -r requirements.txt
```

4. Notebookを上から実行します。

まず軽く確認する場合は `student_ai_colab.ipynb` の mock model 条件から実行してください。LLMを使う場合はGPUとHugging Faceのモデルアクセスが必要になることがあります。

## ColabでGitHub更新を反映する

Colab上のrepoを最新にする場合:

```python
%cd /content/student-ai
!git fetch origin main
!git reset --hard origin/main
!git log -1 --oneline
```

注意: すでに開いているNotebookのセル内容は自動で書き換わらないことがあります。Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。

## 生徒AI単体評価

人間学習者の限定的代理として使えるかを見る基本実験です。

```python
from src.experiment import (
    export_student_ai_evaluation,
    export_student_ai_evaluation_for_codex,
    run_student_ai_evaluation,
)

result = run_student_ai_evaluation(
    student_id="S002",
    test_id="linear_equation_20q_001",
    understanding_levels=list(range(0, 101, 10)),
    use_mock_model=True,
)

export_student_ai_evaluation(result)
export_student_ai_evaluation_for_codex(result)
print(result["summary"])
```

このチャットに結果を渡す場合は、次のファイルを添付してください。

```text
data/assessments/student_ai_evaluation_for_codex.txt
```

従来の認知モデルとBKT/IRT寄りの認知モデルを比較する場合:

```python
from src.experiment import (
    compare_cognitive_models,
    export_cognitive_model_comparison_for_codex,
)

comparison = compare_cognitive_models(
    student_id="S002",
    test_id="linear_equation_20q_001",
    understanding_levels=list(range(0, 101, 10)),
    use_mock_model=True,
)

export_cognitive_model_comparison_for_codex(comparison)
```

共有用ファイル:

```text
data/assessments/cognitive_model_comparison_for_codex.txt
```

出力には次が含まれます。

- Learning Curve
- Difficulty Breakdown
- Misconception Comparison
- Skill Breakdown
- Parameter Guide
- Utterance Samples
- Human Replacement Validity

## LLM設定

ローカルLLMは `transformers` で読み込みます。4bit量子化には `bitsandbytes` を使います。

想定モデル:

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

ColabでLLMを使う場合、初回ロードには時間がかかります。動作確認だけなら `use_mock_model=True` を使ってください。

## 生徒状態

生徒状態は `data/students/{student_id}.json` に保存します。

主なフィールド:

- `knowledge_state`: 一次方程式の理解度。スコアは0-100
- `misconceptions`: 誤概念
- `error_tendency`: 誤答傾向
- `learning_speed`: 学習速度
- `big_five`: Big Five 特性
- `self_efficacy`: 自己効力感
- `question_tendency`: 質問傾向
- `motivation`: モチベーション
- `learning_history`: 学習履歴

性格・心理系の段階評価は原則として `very_low`, `low`, `medium`, `high`, `very_high` の5段階です。

## テスト

通常テストではモデルのダウンロードを行いません。mock modelを使って、状態管理、ログ保存、伝達AI、教師AI、実験ランナーの経路を確認します。

```bash
python -m pytest
```
