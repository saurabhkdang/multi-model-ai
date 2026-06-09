from fastapi import FastAPI
from pydantic import BaseModel
# from agent import run_agent
from agents.manager_agent import run_manager_agent

app = FastAPI(title="Minimal AI Agent")


class AskRequest(BaseModel):
    query: str


@app.get("/")
def home():
    return {
        "message": "Minimal AI Agent is running"
    }


@app.post("/ask")
def ask(request: AskRequest):
    return run_manager_agent(request.query)