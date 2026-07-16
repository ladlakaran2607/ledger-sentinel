import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from graph import builder

load_dotenv()

graph = None
pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, pool
    pool = ConnectionPool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=5,
        kwargs={"autocommit": True, "prepare_threshold": None, "row_factory": dict_row},
    )
    checkpointer = PostgresSaver(pool)
    graph = builder.compile(checkpointer=checkpointer)
    yield
    pool.close()


app = FastAPI(title="Ledger Sentinel runner", lifespan=lifespan)


class StartBody(BaseModel):
    invoice_id: str


class ResumeBody(BaseModel):
    decision: str


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _run_start(invoice_id: str) -> None:
    graph.invoke({"invoice_id": invoice_id, "decision": "", "status": "new"}, _config(invoice_id))


def _run_resume(thread_id: str, decision: str) -> None:
    graph.invoke(Command(resume=decision), _config(thread_id))


@app.get("/meta")
def meta() -> dict:
    return {
        "name": "Ledger Sentinel",
        "description": "AP invoice exception investigator. Human approval required on any payment.",
        "config_schema": {
            "invoice_id": {"type": "string", "required": True, "placeholder": "INV-1059"},
        },
    }


@app.post("/start", status_code=202)
def start(body: StartBody, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_run_start, body.invoice_id)
    return {"thread_id": body.invoice_id}


@app.get("/status/{thread_id}")
def status(thread_id: str) -> dict:
    snapshot = graph.get_state(_config(thread_id))
    values = snapshot.values or {}
    interrupts = [i for task in snapshot.tasks for i in task.interrupts]

    if not values:
        phase = "not_found"
    elif interrupts:
        phase = "waiting_approval"
    elif snapshot.next:
        phase = "running"
    else:
        phase = "complete"

    final = None
    if phase == "complete":
        final = {
            "status": values.get("status"),
            "root_cause": values.get("root_cause"),
            "recommended_action": values.get("recommended_action"),
            "decision": values.get("decision"),
        }

    return {
        "thread_id": thread_id,
        "phase": phase,
        "hops": values.get("hops", 0),
        "evidence": values.get("evidence", []),
        "hypothesis": values.get("hypothesis"),
        "confidence": values.get("confidence"),
        "root_cause": values.get("root_cause"),
        "recommended_action": values.get("recommended_action"),
        "status": values.get("status"),
        "interrupt": interrupts[0].value if interrupts else None,
        "final": final,
    }


@app.post("/resume/{thread_id}", status_code=202)
def resume(thread_id: str, body: ResumeBody, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_run_resume, thread_id, body.decision)
    return {"thread_id": thread_id, "resuming": True}
