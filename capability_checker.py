"""
Medinote -- CapabilityChecker
Logs Mode 3 (unknown intent) requests for future model development.
"""

import json
import logging
from datetime import datetime

log = logging.getLogger("capability_checker")

LOG_PATH = r"c:\Users\omri\Desktop\pii\mode3_requests.jsonl"


class CapabilityChecker:
    def log_mode3(self, user_request: str, task_id: str) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "task_id": task_id,
            "mode": "mode3",
        }
        log.info("Mode3 logged: %s", user_request[:80])
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            log.warning("Could not write mode3 log: %s", exc)
