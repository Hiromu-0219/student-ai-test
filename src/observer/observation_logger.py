from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ObservationLogger:
    def __init__(self, path: str | Path = "data/observations/classroom_events.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def log_event(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.log_event(event)
