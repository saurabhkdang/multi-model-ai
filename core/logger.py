# core/logger.py

import logging
import json
from datetime import datetime

logger = logging.getLogger("hr_ai_agent")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("logs/app.log")
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)


def log_event(event_type: str, data: dict):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        **data
    }

    logger.info(json.dumps(log_data, default=str))