from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from brain import MAX_HOPS, decide, run_tool
from tools import fetch_invoice


class ExceptionState(TypedDict):
    invoice_id: str
    exception_invoice: dict
    evidence: list
    hypothesis: str
    confidence: float
    next_tool: str
    tool_args: dict
    root_cause: str
    recommended_action: str
    hops: int
    decision: str
    status: str


def load_invoice(state: ExceptionState) -> dict:
    return {
        "exception_invoice": fetch_invoice(state["invoice_id"]),
        "evidence": [],
        "hops": 0,
        "status": "investigating",
    }


def investigate(state: ExceptionState) -> dict:
    case_file = {
        "exception_invoice": state["exception_invoice"],
        "evidence": state["evidence"],
    }
    d = decide(case_file)
    hop = state["hops"] + 1
    print(f"\n--- hop {hop} ---")
    print(f"hypothesis: {d['hypothesis']}")
    print(f"confidence: {d['confidence']}")
    if d["next_tool"]:
        print(f"tool call:  {d['next_tool']}({d['tool_args']})")
    else:
        print(f"root cause: {d['root_cause']}")
        print(f"action:     {d['recommended_action']}")
    return {
        "hypothesis": d["hypothesis"],
        "confidence": d["confidence"] or 0.0,
        "next_tool": d["next_tool"],
        "tool_args": d["tool_args"],
        "root_cause": d["root_cause"],
        "recommended_action": d["recommended_action"],
        "hops": hop,
    }


def execute_tool(state: ExceptionState) -> dict:
    result = run_tool(state["next_tool"], state["tool_args"])
    new_evidence = state["evidence"] + [{
        "hop": state["hops"],
        "hypothesis": state["hypothesis"],
        "tool": state["next_tool"],
        "args": state["tool_args"],
        "result": result,
    }]
    return {"evidence": new_evidence}


def route_after_investigate(state: ExceptionState) -> str:
    if state["next_tool"]:
        if state["hops"] >= MAX_HOPS:
            return "escalate"
        return "execute_tool"
    if state["recommended_action"] == "request_release_approval":
        return "approval_gate"
    if state["recommended_action"] in (None, "escalate_low_confidence"):
        return "escalate"
    return "close_case"


def approval_gate(state: ExceptionState) -> dict:
    inv = state["exception_invoice"]
    decision = interrupt({
        "question": "Approve this payment?",
        "invoice_id": state["invoice_id"],
        "vendor_id": inv["vendor_id"],
        "amount": inv["total"],
        "root_cause": state["root_cause"],
        "evidence_hops": state["hops"],
    })
    return {"decision": decision, "status": "decided"}


def route_decision(state: ExceptionState) -> str:
    if state["decision"] == "approved":
        return "execute_release"
    return "log_rejection"


def execute_release(state: ExceptionState) -> dict:
    inv = state["exception_invoice"]
    print(f"EXECUTING: releasing ${inv['total']:,.2f} to {inv['vendor_id']} for {state['invoice_id']}")
    return {"status": "released"}


def log_rejection(state: ExceptionState) -> dict:
    print(f"REJECTED: release for {state['invoice_id']} will not be executed")
    return {"status": "rejected"}


def close_case(state: ExceptionState) -> dict:
    print(f"CLOSED: {state['invoice_id']} -> {state['recommended_action']}")
    print(f"        {state['root_cause']}")
    return {"status": state["recommended_action"]}


def escalate(state: ExceptionState) -> dict:
    print(f"ESCALATED: {state['invoice_id']} needs human review")
    print(f"           {state['root_cause']}")
    return {"status": "escalated"}


builder = StateGraph(ExceptionState)
builder.add_node("load_invoice", load_invoice)
builder.add_node("investigate", investigate)
builder.add_node("execute_tool", execute_tool)
builder.add_node("approval_gate", approval_gate)
builder.add_node("execute_release", execute_release)
builder.add_node("log_rejection", log_rejection)
builder.add_node("close_case", close_case)
builder.add_node("escalate", escalate)

builder.add_edge(START, "load_invoice")
builder.add_edge("load_invoice", "investigate")
builder.add_conditional_edges("investigate", route_after_investigate,
                              ["execute_tool", "approval_gate", "close_case", "escalate"])
builder.add_edge("execute_tool", "investigate")
builder.add_conditional_edges("approval_gate", route_decision,
                              ["execute_release", "log_rejection"])
builder.add_edge("execute_release", END)
builder.add_edge("log_rejection", END)
builder.add_edge("close_case", END)
builder.add_edge("escalate", END)