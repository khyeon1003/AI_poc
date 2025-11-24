# export_rag_log.py
import json
from database import SessionLocal
from models.rag_log import RagLogModel

def export_rag_logs_to_json(output_path="rag_logs.json"):
    db = SessionLocal()
    try:
        rows = db.query(RagLogModel).order_by(RagLogModel.created_at).all()

        result = []
        for r in rows:
            result.append({
                "id": str(r.id),
                "request_id": r.request_id,
                "created_at": r.created_at.isoformat(),
                "log": r.log,  # JSONB 그대로
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✔ JSON Export completed → {output_path}")

    finally:
        db.close()


if __name__ == "__main__":
    export_rag_logs_to_json()
