from sqlalchemy import text
from database import SessionLocal

def init_hnsw_index():
    sql = """
    CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding_hnsw
    ON doc_chunks
    USING hnsw (embedding vector_cosine_ops);
    """
    db = SessionLocal()
    db.execute(text(sql))
    db.commit()
    db.close()
