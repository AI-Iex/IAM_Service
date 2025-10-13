import logging
import json
from typing import Any
from app.middleware.logging import RequestIdFilter

class JSONFormatter(logging.Formatter):
    # Custom JSON formatter that includes request_id if available
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        
        extras = {k: v for k, v in record.__dict__.items()
                  if k not in ("name","msg","args","levelname","levelno","pathname",
                               "filename","module","exc_info","exc_text","stack_info",
                               "lineno","funcName","created","msecs","relativeCreated",
                               "thread","threadName","processName","process")}
        if extras:
            payload["extra"] = extras
       
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

def setup_logging(level: int = logging.INFO) -> None:
    # Configure root logger with JSON formatter and RequestIdFilter
    root = logging.getLogger()
    root.setLevel(level)

    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(JSONFormatter())
        root.addHandler(stream_handler)

    # Add RequestIdFilter to all handlers
    request_id_filter = RequestIdFilter()
    for h in root.handlers:
        h.addFilter(request_id_filter)
