# util/ocr_store.py
import json
from pathlib import Path
from datetime import datetime

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "ocr_results.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_ocr_record(title: str, image_url: str, ocr_text: str) -> None:
    record = {
        "title": title,
        "image_url": image_url,
        "ocr_text": ocr_text,
        "logged_at": datetime.utcnow().isoformat(), # noqa
    }

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
