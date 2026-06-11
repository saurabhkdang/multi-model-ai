# middleware/logging_middleware.py

import time
import uuid
from fastapi import Request
from core.logger import log_event

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    request.state.request_id = request_id

    log_event("REQUEST_STARTED", {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method
    })

    response = await call_next(request)

    total_time_ms = round((time.time() - start_time) * 1000, 2)

    log_event("REQUEST_COMPLETED", {
        "request_id": request_id,
        "status_code": response.status_code,
        "total_time_ms": total_time_ms
    })

    return response