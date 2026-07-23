# Student AI Education Simulation

一次方程式を題材に、生徒AI・伝達AI・講義設計AI・教師発話AIを組み合わせて授業シミュレーションを行う研究用リポジトリです。

現在の主張範囲は、人間生徒の完全な代替ではありません。理解度、誤概念、個人特徴を外部状態として制御した生徒AIが、教育シミュレーション内の「限定的な学習者代理」として使えるかを内部妥当性から検証します。

## まず読むもの

| 目的 | ファイル |
| --- | --- |
| 生徒AIの設計を把握する | [docs/student_ai_design.md](docs/student_ai_design.md) |
| 進捗報告として共有する | [docs/student_ai_progress_report.md](docs/student_ai_progress_report.md) |
| 論文用の実験コアを見る | [docs/paper_experiment_core.md](docs/paper_experiment_core.md) |
| 内部妥当性の評価方法を見る | [docs/internal_validity_experiment.md](docs/internal_validity_experiment.md) |
| 参考文献との対応を見る | [docs/reference_mapping.md](docs/reference_mapping.md) |
| Notebookの使い分けを見る | [notebooks/README.md](notebooks/README.md) |

## 全体構成

```text
student-ai/
  README.md
  AGENTS.md
  requirements.txt
  data/
    students/          # 生徒ごとの内部状態
    classes/           # クラス構成とクラス特徴
    teacher_beliefs/   # 教師側が観察から持つ生徒理解
    tests/             # 一次方程式テスト
    curriculum/        # 単元・スキル定義
    logs/              # 対話ログ
    assessments/       # 実験結果・共有用txt
  docs/
    daily/             # 日付ごとの作業メモ
  notebooks/
    student_ai_colab.ipynb
    personality_experiment.ipynb
    teaching_strategy_experiment.ipynb
    paper_core_experiment.ipynb
  src/
    experiment/        # 論文・検証用実験ランナー
    observer/          # 伝達AI、観察情報フィルタ
    teacher/           # 講義設計AI、教師AI関連
  tests/
```

## シミュレーションの流れ

```text
生徒AI
  -> 授業中に観察できる発話・正誤・反応を出す
伝達AI
  -> 観察可能情報だけから、生徒個人とクラス全体を要約する
講義設計AI
  -> クラス全体に対して次の授業構成を考える
教師発話AI
  -> 授業構成に沿って全体・個別の発話を作る
生徒AI
  -> 教師発話を受けて反応する
```

生徒AIの内部状態は `data/students/*.json` で管理し、LLMは主に発話生成器として使います。理解度と正答は `src/cognitive_model.py` の認知モデルで制御します。

## Notebookの役割

| Notebook | 役割 |
| --- | --- |
| `notebooks/student_ai_colab.ipynb` | 生徒AI単体の設計確認、学習曲線、誤概念、難易度別正答率、発話サンプル |
| `notebooks/personality_experiment.ipynb` | 個人特徴が発話に出るか、伝達AIが分類できるかを確認 |
| `notebooks/teaching_strategy_experiment.ipynb` | 複数生徒クラス、伝達AI要約、講義設計AI、教師発話AIの流れを確認 |
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

4. Notebookを開きます。

まずは `notebooks/student_ai_colab.ipynb` で生徒AI単体の評価を確認してください。LLMロードは時間がかかるため、最初は `use_mock_model=True` のセルだけで動作確認するのがおすすめです。

## ColabでGitHub更新を反映する

Colab上のrepoを最新にする場合:

```python
%cd /content/student-ai
!git fetch origin main
!git reset --hard origin/main
!git log -1 --oneline
```

すでに開いているNotebook画面のセル内容は自動更新されないことがあります。Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。

## LLM設定

ローカルLLMは `transformers` で読み込みます。4bit量子化は `bitsandbytes` の `BitsAndBytesConfig` を使います。

想定モデル:

- `Qwen/Qwen3-4B`
- `google/gemma-3-4b-it`

Gemma系の gated model を使う場合は、Colab上で Hugging Face login が必要になることがあります。

## テスト

標準テストではモデルダウンロードを行いません。mock modelで状態管理、ログ保存、実験ランナーの経路を確認します。

```bash
python -m pytest
```
