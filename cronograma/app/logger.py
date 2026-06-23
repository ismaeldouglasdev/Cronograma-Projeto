"""
Sistema de Logging Estruturado para Cronograma App.

Recursos:
- Logs em formato JSON para fácil parse
- Rotação automática de arquivos (7 dias de retenção)
- Níveis: DEBUG, INFO, WARNING, ERROR
- Contexto enriquecido: user_id, endpoint, IP, duração
- Dois handlers: console (cores) + arquivo (JSON)
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Constants ────────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "cronograma.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 7
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── JSON Formatter ───────────────────────────────────────────────────────────


class JsonFormatter(logging.Formatter):
    """Formata logs como JSON com campos padronizados."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Extra attributes from record (set via extra={})
        for key in ("user_id", "endpoint", "method", "status_code", "duration_ms",
                     "ip", "error_type", "request_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        # Include exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Formata logs para console com cores."""
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Short level (e.g. INFO -> I)
        level_short = record.levelname[0]

        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        base = f"{color}{level_short}{reset} {timestamp} {record.getMessage()}"

        # Append extra context for console
        extras = []
        for key in ("user_id", "endpoint", "status_code", "duration_ms"):
            if hasattr(record, key):
                val = getattr(record, key)
                extras.append(f"{key}={val}")

        if record.exc_info and record.exc_info[0]:
            extras.append(
                f"error={record.exc_info[0].__name__}: {record.exc_info[1]}"
            )

        if extras:
            base += f" {color}[{' '.join(extras)}]{reset}"

        return base


# ─── Logger Factory ───────────────────────────────────────────────────────────


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado com:
      - Handler de arquivo (JSON rotation)
      - Handler de console (colorido)
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler (JSON)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(LOG_LEVEL)
    logger.addHandler(file_handler)

    # Console handler (colorido)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    console_handler.setLevel(LOG_LEVEL)
    logger.addHandler(console_handler)

    return logger


# ─── Convenience Helpers ──────────────────────────────────────────────────────

_loggers_cache: dict[str, logging.Logger] = {}


def audit(action: str, user_id: Optional[int] = None, **kwargs):
    """
    Log de auditoria para operações críticas.
    Ex: audit("area.delete", user_id=1, area_id=5, area_nome="Matemática")
    """
    logger = _loggers_cache.get("audit")
    if not logger:
        logger = get_logger("audit")
        _loggers_cache["audit"] = logger

    extra = {"user_id": user_id, **kwargs}
    logger.info(f"AUDIT {action}", extra=extra)


def log_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[int] = None,
    ip: Optional[str] = None,
):
    """Log de requisição HTTP."""
    logger = _loggers_cache.get("request")
    if not logger:
        logger = get_logger("request")
        _loggers_cache["request"] = logger

    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 1),
        "user_id": user_id,
        "ip": ip,
    }
    level = logging.ERROR if status_code >= 500 else (
        logging.WARNING if status_code >= 400 else logging.INFO
    )
    logger.log(level, f"{method} {endpoint} {status_code}", extra=extra)


# ─── Exported API ─────────────────────────────────────────────────────────────

__all__ = [
    "get_logger",
    "audit",
    "log_request",
    "LOG_DIR",
    "LOG_FILE",
]
