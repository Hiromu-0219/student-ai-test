# Notebook Guide

研究の流れが分かるように、既存Notebookを次の役割で使います。

| 順番 | Notebook | 目的 |
| --- | --- | --- |
| 00 | `paper_core_experiment.ipynb` | 論文用の最小実験、使用ソースコード、確認観点を整理する |
| 01 | `student_ai_colab.ipynb` | 生徒AIの内部状態、パラメータ、回答生成を確認する |
| 02 | `student_ai_colab.ipynb` | 理解度と正答率の学習曲線を確認する |
| 03 | `personality_experiment.ipynb` | 個人特徴が発話に反映され、伝達AIが分類できるか確認する |
| 04 | `teaching_strategy_experiment.ipynb` | 複数生徒クラス、伝達AI要約、教師AIの授業方略を確認する |

## 実行の考え方

まず `paper_core_experiment.ipynb` で研究のコアを確認します。
その後、`student_ai_colab.ipynb` で生徒AI単体の制御妥当性を確認し、
`personality_experiment.ipynb` で個人特徴の推定可能性を見ます。
最後に `teaching_strategy_experiment.ipynb` で複数生徒クラスに対する授業方略生成を確認します。

ColabでNotebook自体を更新した場合、Git更新セルだけでは開いているNotebook画面のセル内容は変わらないことがあります。
その場合はGitHub上の最新版Notebookを開き直してください。
