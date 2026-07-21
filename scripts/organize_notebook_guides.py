from __future__ import annotations

import json
from pathlib import Path


UPDATED_AT = "2026-07-21 09:58:48 JST"
GUIDE_MARKER = "<!-- notebook-role-guide -->"


NOTEBOOK_GUIDES = {
    "student_ai_colab.ipynb": {
        "title": "# 01-02 生徒AI設計・学習曲線確認ノートブック",
        "description": "一次方程式の生徒AIについて、内部パラメータの設計と理解度-正答率の関係を確認するNotebookです。",
        "purpose": [
            "生徒状態JSONの構造を確認する",
            "理解度、誤概念、個人特徴が回答にどう影響するかを見る",
            "理解度0-100と正答率の学習曲線を確認する",
        ],
        "run_order": [
            "Colabでは 1-3 を先に実行して環境を作る",
            "設計確認は 5-10 を実行する",
            "学習曲線は 12-15 を実行する",
            "Git更新やテストは 17-18 を必要な時だけ実行する",
        ],
        "output": [
            "生徒AIの内部状態",
            "1問ごとの回答",
            "理解度と正答率の表・グラフ",
            "誤答傾向の確認結果",
        ],
    },
    "personality_experiment.ipynb": {
        "title": "# 03 個人特徴・伝達AI分類実験ノートブック",
        "description": "知識状態をそろえた生徒に異なる個人特徴を持たせ、発話から伝達AIが特徴を推定できるか確認するNotebookです。",
        "purpose": [
            "自己効力感、質問傾向、モチベーションなどを発話に反映する",
            "伝達AIが発話だけから個人特徴を分類できるか見る",
            "別AIや人間評価者に渡す分類用プロンプトを作る",
        ],
        "run_order": [
            "Colabでは 1-2 を先に実行する",
            "発話生成は 3-4 を実行する",
            "伝達AI分類は 5-6 を実行する",
            "外部評価用プロンプトは 7 を実行する",
        ],
        "output": [
            "個人特徴ごとの発話サンプル",
            "伝達AIの分類結果",
            "正解ラベルと推定結果の比較材料",
        ],
    },
    "teaching_strategy_experiment.ipynb": {
        "title": "# 04 授業方略メイン実験ノートブック",
        "description": "複数生徒の授業中反応を伝達AIが要約し、教師AIが授業構成と個別支援を決める流れを確認するメインNotebookです。",
        "purpose": [
            "複数生徒の観察可能な反応だけを使う",
            "伝達AIがクラス全体と個人の特徴を要約する",
            "教師AIが要約に基づいて授業構成・支援方針・発話を生成する",
        ],
        "run_order": [
            "Colabでは 1-3 を先に実行する",
            "主実験は 4-7, 9, 11-12, 17 を実行する",
            "8, 10, 13-16 は重い確認用なので必要な時だけ実行する",
            "結果共有は最後のサマリー保存セルを実行する",
        ],
        "output": [
            "生徒発話",
            "伝達AIのクラス要約",
            "教師AIの授業構成",
            "個別支援方針",
            "共有用txtサマリー",
        ],
    },
    "paper_core_experiment.ipynb": {
        "title": "# 00 論文用コア確認ノートブック",
        "description": "論文で説明する実験の最小構成、使用ソースコード、確認観点をまとめるNotebookです。",
        "purpose": [
            "研究のコア実験だけを確認する",
            "使用するソースコードと実験条件を対応づける",
            "論文に載せる比較表や確認ポイントを作る",
        ],
        "run_order": [
            "Colabでは 0 を先に実行する",
            "実験の概要確認は 1-4 を実行する",
            "授業構成比較は 6-9 を実行する",
            "LLMの確認は 5 を必要な時だけ実行する",
        ],
        "output": [
            "論文用の実験条件",
            "クラス条件ごとの授業構成比較",
            "論文に使う確認ポイント",
        ],
    },
}


def markdown_cell(source: str) -> dict:
    if not source.endswith("\n"):
        source += "\n"
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_top_markdown(guide: dict) -> str:
    return "\n".join(
        [
            guide["title"],
            "",
            f"最終更新: {UPDATED_AT}",
            "",
            guide["description"],
            "",
            "このNotebookは研究全体の一部です。単独でも動きますが、論文用には以下の順番で確認します。",
            "",
            "```text",
            "00 paper_core_experiment.ipynb       : 論文用の最小実験整理",
            "01 student_ai_colab.ipynb            : 生徒AIの設計確認",
            "02 student_ai_colab.ipynb            : 理解度と正答率の学習曲線確認",
            "03 personality_experiment.ipynb      : 個人特徴と伝達AI分類",
            "04 teaching_strategy_experiment.ipynb: 複数生徒クラスと授業方略",
            "```",
        ]
    )


def build_guide_markdown(guide: dict) -> str:
    return "\n".join(
        [
            GUIDE_MARKER,
            "## このNotebookで確認すること",
            "",
            bullet_list(guide["purpose"]),
            "",
            "## 実行順",
            "",
            bullet_list(guide["run_order"]),
            "",
            "## 主な出力",
            "",
            bullet_list(guide["output"]),
            "",
            "## 注意",
            "",
            "- ColabでGit更新セルを実行しても、すでに開いているNotebook画面のセル内容は自動では書き換わりません。",
            "- Notebook自体を更新した場合は、GitHub上の最新版Notebookを開き直してください。",
            "- LLMを使うセルはロードに時間がかかります。まずはmockまたは軽量モデルで確認してください。",
        ]
    )


def update_notebook(path: Path, guide: dict) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["cells"][0] = markdown_cell(build_top_markdown(guide))

    guide_index = next(
        (
            index
            for index, cell in enumerate(notebook["cells"])
            if GUIDE_MARKER in cell_source(cell)
        ),
        None,
    )
    guide_cell = markdown_cell(build_guide_markdown(guide))
    if guide_index is None:
        notebook["cells"].insert(1, guide_cell)
    else:
        notebook["cells"][guide_index] = guide_cell

    path.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"updated {path}")


def main() -> None:
    for filename, guide in NOTEBOOK_GUIDES.items():
        update_notebook(Path("notebooks") / filename, guide)


if __name__ == "__main__":
    main()
