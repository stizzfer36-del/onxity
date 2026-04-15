from __future__ import annotations

import json
import time
import uuid

from sqlalchemy import Float, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


class MemoryChunk(Base):
    __tablename__ = "memory_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    start_ts: Mapped[float] = mapped_column(Float)
    end_ts: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float, default=0.0)


class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String)
    tool: Mapped[str] = mapped_column(String)
    args_redacted: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String)
    ts: Mapped[float] = mapped_column(Float, default=time.time)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String)
    created_ts: Mapped[float] = mapped_column(Float, default=time.time)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text)
    ts: Mapped[float] = mapped_column(Float, default=time.time)


_engine = None
SessionLocal = None


def init_db(db_url: str):
    global _engine, SessionLocal
    _engine = create_engine(db_url, future=True)
    Base.metadata.create_all(_engine)
    SessionLocal = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False))
    with _engine.begin() as conn:
        try:
            conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks_fts USING fts5(id, content)"))
        except Exception:
            pass
    return SessionLocal


def get_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized")
    return SessionLocal()


def add_memory_chunk(db, content: str, start_ts: float, end_ts: float, score: float = 0.0) -> str:
    cid = f"chunk-{uuid.uuid4().hex[:8]}"
    row = MemoryChunk(id=cid, content=content, start_ts=start_ts, end_ts=end_ts, score=score)
    db.add(row)
    db.commit()
    try:
        db.execute(text("INSERT INTO memory_chunks_fts(id, content) VALUES (:id,:content)"), {"id": cid, "content": content})
        db.commit()
    except Exception:
        pass
    return cid


def add_audit_db(db, typ: str, payload: dict):
    db.add(AuditLog(id=str(uuid.uuid4()), type=typ, payload_json=json.dumps(payload), ts=time.time()))
    db.commit()
