import json
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

from prompts import INVESTIGATOR_SYSTEM
from tools import (
    fetch_goods_receipts,
    fetch_invoice,
    fetch_po,
    read_contract_clauses,
    search_vendor_history,
    three_way_match,
)

TOOL_REGISTRY = {
    "three_way_match": three_way_match,
    "fetch_po": fetch_po,
    "fetch_goods_receipts": fetch_goods_receipts,
    "read_contract_clauses": read_contract_clauses,
    "search_vendor_history": search_vendor_history,
}

MODEL = "claude-sonnet-5"
MAX_HOPS = 8

client = Anthropic()

DECISION_KEYS = ("hypothesis", "confidence", "next_tool", "tool_args",
                 "root_cause", "recommended_action", "reasoning")

def parse_decision(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in model output: {text[:200]}")
    return json.loads(text[start:end + 1])

def decide(case_file: dict) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=INVESTIGATOR_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(case_file, indent=2)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    decision = parse_decision(text)
    for key in DECISION_KEYS:
        decision.setdefault(key, None)
    return decision

def run_tool(tool_name: str, tool_args: dict) -> dict:
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if tool_fn is None:
        return {"error": f"unknown tool '{tool_name}', valid tools: {list(TOOL_REGISTRY)}"}
    try:
        return tool_fn(**(tool_args or {}))
    except TypeError as e:
        return {"error": f"bad arguments for {tool_name}: {e}"}

def run_investigation(invoice_id: str) -> dict:
    case_file = {"exception_invoice": fetch_invoice(invoice_id), "evidence": []}

    for hop in range(1, MAX_HOPS + 1):
        decision = decide(case_file)
        print(f"\n--- hop {hop} ---")
        print(f"hypothesis: {decision['hypothesis']}")
        print(f"confidence: {decision['confidence']}")
        print(f"reasoning:  {decision['reasoning']}")

        if decision["next_tool"] is None:
            print(f"root cause: {decision['root_cause']}")
            print(f"action:     {decision['recommended_action']}")
            return {"invoice_id": invoice_id, "hops": hop, **decision}

        print(f"tool call:  {decision['next_tool']}({decision['tool_args']})")
        result = run_tool(decision["next_tool"], decision["tool_args"])
        case_file["evidence"].append({
            "hop": hop,
            "hypothesis": decision["hypothesis"],
            "tool": decision["next_tool"],
            "args": decision["tool_args"],
            "result": result,
        })

    return {
        "invoice_id": invoice_id,
        "hops": MAX_HOPS,
        "root_cause": "investigation exceeded maximum probes without conclusion",
        "recommended_action": "escalate_low_confidence",
    }

if __name__ == "__main__":
    invoice_id = sys.argv[1] if len(sys.argv) > 1 else "INV-1051"
    final = run_investigation(invoice_id)
    print(f"\n=== FINAL ({final['invoice_id']}, {final['hops']} hops) ===")
    print(json.dumps({k: v for k, v in final.items() if k != "hops"}, indent=2))