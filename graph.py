from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt


class ExceptionState(TypedDict):
    invoice_id: str
    vendor: str
    amount: float
    proposed_action: str
    decision: str
    status: str


def draft_release(state: ExceptionState) -> dict:
    action = f"Release ${state['amount']:,.2f} to {state['vendor']} for {state['invoice_id']}"
    return {"proposed_action": action, "status": "drafted"}


def approval_gate(state: ExceptionState) -> dict:
    decision = interrupt({
        "question": "Approve this payment?",
        "action": state["proposed_action"],
        "amount": state["amount"],
        "vendor": state["vendor"],
    })
    return {"decision": decision, "status": "decided"}


def route_decision(state: ExceptionState) -> str:
    if state["decision"] == "approved":
        return "execute_release"
    return "log_rejection"


def execute_release(state: ExceptionState) -> dict:
    print(f"EXECUTING: {state['proposed_action']}")
    return {"status": "released"}


def log_rejection(state: ExceptionState) -> dict:
    print(f"REJECTED: {state['proposed_action']} will not be executed")
    return {"status": "rejected"}


builder = StateGraph(ExceptionState)
builder.add_node("draft_release", draft_release)
builder.add_node("approval_gate", approval_gate)
builder.add_node("execute_release", execute_release)
builder.add_node("log_rejection", log_rejection)

builder.add_edge(START, "draft_release")
builder.add_edge("draft_release", "approval_gate")
builder.add_conditional_edges("approval_gate", route_decision, ["execute_release", "log_rejection"])
builder.add_edge("execute_release", END)
builder.add_edge("log_rejection", END)