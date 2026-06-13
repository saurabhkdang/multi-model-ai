from fastapi import FastAPI, Request
from pydantic import BaseModel
from core.followup_resolver import resolve_followup_query
from memory import get_memory_context
from agents.manager_agent import run_manager_agent
from middleware.logging_middleware import logging_middleware
from core.followup_resolver import resolve_followup_query

app = FastAPI(title="Minimal AI Agent")
app.middleware("http")(logging_middleware)

class AskRequest(BaseModel):
    query: str
    debug: bool = False


@app.get("/")
def home():
    return {
        "message": "Minimal AI Agent is running"
    }


@app.post("/ask")
async def ask(payload: AskRequest, request: Request):
    request_id = request.state.request_id
    memory_context = get_memory_context()

    resolved_question = resolve_followup_query(
        user_query=payload.query,
        memory_context=memory_context,
        request_id=request_id
    )
    
    result = run_manager_agent(
        user_query=resolved_question['resolved_query'],
        request_id=request_id,
        debug=payload.debug
    )

    if payload.debug:
        result["debug"]["original_query"] = payload.query
        result["debug"]["resolved_question"] = resolved_question
        result["debug"]["memory_context_before"] = memory_context

    return result
    # return run_manager_agent(request.query)