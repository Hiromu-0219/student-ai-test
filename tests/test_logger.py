import json

from src.logger import AnswerLogger


def test_log_interaction_writes_jsonl_and_markdown(tmp_path):
    logger = AnswerLogger(tmp_path)

    record = logger.log_interaction(
        student_id="S001",
        problem="2x + 3 = 11",
        answer="答え: x = 4",
        student_state_snapshot={
            "student_id": "S001",
            "understanding": {},
            "error_tendency": [],
            "personality": {},
            "learning_history": [],
        },
        model_id="test-model",
    )

    jsonl_lines = logger.jsonl_path.read_text(encoding="utf-8").splitlines()
    markdown = logger.markdown_path.read_text(encoding="utf-8")

    assert json.loads(jsonl_lines[0])["student_id"] == "S001"
    assert record["answer"] in markdown
    assert "2x + 3 = 11" in markdown
