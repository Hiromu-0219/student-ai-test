# 教育シミュレーション研究

最終更新: 2026-10-01 JST

複数の生徒AIを観察し、伝達AIの要約を使って教師がクラス全体の授業を調整する研究です。生徒の認知・行動・性格を外部状態で制御し、LLMで発話を生成します。対象単元は一次方程式です。

## 最初に読む

- [研究の目的・評価・次にやること](docs/research_overview.md)
- [生徒AIの設計仕様](docs/design/student_ai_design.md)
- [参考文献と設計の対応](docs/design/reference_mapping.md)
- 別端末への引継ぎ: [CODEX_HANDOFF.md](CODEX_HANDOFF.md)

## 実行するNotebookは3つ

| Notebook | 用途 |
| --- | --- |
| [授業シミュレーション](notebooks/simulation_timeline_experiment.ipynb) | 最初に実行。時間経過、会話、授業設計を確認 |
| [伝達AIの評価](notebooks/communication_ai_rq1_experiment.ipynb) | 観察からの生徒状態推定を比較 |
| [生徒AIの発表実験](notebooks/student_ai_presentation_experiment.ipynb) | 認知モデルの式、正答率、性格別発話、複数生徒の分布 |

詳細な旧実験は `notebooks/supplementary/` に保存しています。

## Colabで実行

1. GitHub上の対象NotebookをColabで開く。
2. LLMを使用する場合は「ランタイム → ランタイムのタイプを変更」でGPUを選ぶ。
3. 上からセットアップ・設定・実験セルを実行する。最初はmockで確認する。
4. LLMを使う設定を有効にして再実行する。GPUなしの代替実行はLLM評価には含めない。
5. `data/assessments/` に出る共有用 `.txt` と会話ログを確認する。

セットアップセルがGitHubから取得するリポジトリ:
`https://github.com/Hiromu-0219/student-ai-test.git`

コード更新はNotebookの更新セルを使います。開いているセル内容は自動更新されないため、Notebook自体の変更はGitHubの最新版をColabで開き直してください。

## ファイルの場所

| フォルダ | 内容 |
| --- | --- |
| `src/` | 生徒AI、認知・行動モデル、伝達AI、教師AI、実験ランナー |
| `data/students/`, `data/classes/` | 生徒の内部状態とクラス構成 |
| `data/teacher_beliefs/` | 観察から得た教師側の推定 |
| `data/assessments/`, `data/logs/` | 実験結果と会話ログ |
| `docs/design/`, `docs/evaluation/` | 設計仕様と詳細評価手順 |
| `docs/archive/`, `docs/daily/` | 過去の計画・報告と作業履歴 |
| `scripts/`, `tests/` | Notebook外の実験実行と自動テスト |

標準テスト: `python -m pytest`。モデルのダウンロードは行いません。

実生徒との一致を証明した段階ではありません。現在は制御可能性と内部整合性を検証します。
