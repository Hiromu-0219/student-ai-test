# src

実装コードの置き場です。Notebookからは基本的に `src.*` をimportして使います。

## 主要モジュール

| パス | 役割 |
| --- | --- |
| `student_ai.py` | 生徒AIの高レベル実行インターフェース |
| `student_agent.py` | 教師入力に対して生徒状態を使って回答を作るエージェント |
| `cognitive_model.py` | 理解度、誤概念、難易度、スキル弱点から正答確率を決める認知モデル |
| `personality_model.py` | 個人特徴を発話スタイルへ反映するモデル |
| `model_loader.py` | transformersによるLLMロードと生成 |
| `state_manager.py` | `data/students/*.json` の読み書き |
| `class_manager.py` | `data/classes/*.json` の読み込みとクラス特徴の取得 |
| `test_bank.py` / `test_runner.py` | テスト問題と評価実行 |
| `grader.py` | 生徒回答の採点 |
| `logger.py` / `assessment_logger.py` | 対話ログ、テストログの保存 |

## サブパッケージ

| パス | 役割 |
| --- | --- |
| `observer/` | 伝達AI。授業中に観察できる情報だけから生徒・クラスを要約する |
| `teacher/` | 講義設計AI、教師発話AI、介入方針、教師側beliefの管理 |
| `experiment/` | 論文・検証用の実験ランナーと結果エクスポート |

## 設計上の注意

- 生徒の真の内部状態は `data/students/*.json` にあり、伝達AI・教師AIは原則として直接参照しません。
- 伝達AI・教師AIは、発話、正誤、授業中の観察イベント、過去のteacher beliefから判断します。
- LLMは主に発話生成・分類補助として使い、理解度と正答確率の制御は認知モデル側で行います。
