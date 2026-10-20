"""Testes do rate limiter persistente e da configuração de CORS."""

import json
import time

from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from middleware import RateLimiter, setup_cors


def _make_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/ratelimit.db",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE rate_limit_buckets ("
                "key TEXT PRIMARY KEY, hits TEXT NOT NULL, "
                "updated_at FLOAT NOT NULL)"
            )
        )
    return sessionmaker(bind=engine), engine


def test_contador_sobrevive_a_restart(tmp_path):
    factory, engine = _make_factory(tmp_path)

    limiter = RateLimiter(persist=True, session_factory=factory)
    for _ in range(3):
        assert limiter.check("k1", max_requests=3, window_seconds=60) is True
    assert limiter.check("k1", max_requests=3, window_seconds=60) is False
    limiter.flush()

    restarted = RateLimiter(persist=True, session_factory=factory)
    assert restarted.check("k1", max_requests=3, window_seconds=60) is False

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT key, hits FROM rate_limit_buckets WHERE key = 'k1'")
        ).fetchall()
    assert len(rows) == 1
    hits = json.loads(rows[0][1])
    assert len(hits) == 3


def test_janela_expirada_nao_bloqueia(tmp_path):
    factory, _ = _make_factory(tmp_path)

    limiter = RateLimiter(persist=True, session_factory=factory)
    old = time.time() - 120.0
    limiter._store["k2"] = [old, old, old]
    limiter._dirty.add("k2")
    limiter.flush()

    restarted = RateLimiter(persist=True, session_factory=factory)
    assert restarted.check("k2", max_requests=3, window_seconds=60) is True


def test_flush_remove_linhas_velhas(tmp_path):
    factory, engine = _make_factory(tmp_path)

    limiter = RateLimiter(persist=True, session_factory=factory)
    ancient = time.time() - 7200.0
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO rate_limit_buckets (key, hits, updated_at) "
                "VALUES ('velha', :h, :t)"
            ),
            {"h": json.dumps([ancient]), "t": ancient},
        )

    limiter.check("nova", max_requests=5, window_seconds=60)
    limiter.flush()

    with engine.connect() as conn:
        remaining = {
            r[0]
            for r in conn.execute(text("SELECT key FROM rate_limit_buckets"))
        }
    assert "velha" not in remaining
    assert "nova" in remaining


def test_persistencia_desligada_sob_pytest():
    limiter = RateLimiter()
    assert limiter._persist is False
    limiter.check("mem-only", max_requests=2)
    limiter.flush()


def test_cors_allow_headers_restringido():
    app = FastAPI()
    setup_cors(app)
    cors = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )
    assert "*" not in cors.kwargs["allow_headers"]
    assert "Authorization" in cors.kwargs["allow_headers"]
    assert "Content-Type" in cors.kwargs["allow_headers"]
