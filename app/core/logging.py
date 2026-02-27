import logging
import sys

from pythonjsonlogger import json as json_log

from app.core.config import settings


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        formatter = json_log.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
        handler.setFormatter(formatter)
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, handlers=[handler], force=True)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )
