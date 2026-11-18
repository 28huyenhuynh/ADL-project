"""
Saved conversations ("Past readings" in the web page).

Each conversation is one JSON file in CHAT_DIR (default: chat_history/), so it survives
browser resets and server restarts; in Docker the folder is a volume. The app runs on
your own machine and has no user accounts, so everyone who can open the page sees the
same saved conversations.
"""

import json
import re
import time
from pathlib import Path

ID = re.compile(r"^[a-z0-9]{8,40}$")      # ids come from the browser: no paths, no dots
MAX_BYTES = 2_000_000                     # one conversation file
MAX_TURNS = 500
TURN_KEYS = {"question", "answer", "sources", "card", "declined", "unsupported",
             "question_en", "scope", "lang", "time"}


class ChatStore:
    def __init__(self, folder: str):
        self.dir = Path(folder)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, chat_id: str) -> Path:
        if not ID.match(chat_id or ""):
            raise ValueError("bad chat id")
        return self.dir / f"{chat_id}.json"

    def list(self, limit: int = 200) -> list[dict]:
        items = []
        for path in self.dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            items.append({"id": data.get("id", path.stem), "title": data.get("title", ""),
                          "created": data.get("created"), "updated": data.get("updated"),
                          "turns": len(data.get("turns", []))})
        items.sort(key=lambda c: c.get("updated") or 0, reverse=True)
        return items[:limit]

    def get(self, chat_id: str) -> dict | None:
        path = self._path(chat_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, chat_id: str, body: dict) -> dict:
        path = self._path(chat_id)
        turns = [{k: v for k, v in t.items() if k in TURN_KEYS}
                 for t in (body.get("turns") or [])[:MAX_TURNS] if isinstance(t, dict) and t.get("question")]
        old = self.get(chat_id) or {}
        now = int(time.time() * 1000)
        data = {
            "id": chat_id,
            "title": (turns[0]["question"] if turns else "")[:90],
            "created": old.get("created") or body.get("created") or now,
            "updated": now,
            "turns": turns,
        }
        text = json.dumps(data, ensure_ascii=False, indent=1)
        if len(text.encode("utf-8")) > MAX_BYTES:
            raise ValueError("conversation too large")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)                    # write-then-rename: never a half-written file
        return {k: data[k] for k in ("id", "title", "created", "updated")}

    def delete(self, chat_id: str) -> bool:
        path = self._path(chat_id)
        if path.exists():
            path.unlink()
            return True
        return False
