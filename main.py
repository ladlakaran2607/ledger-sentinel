import os
import sys

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from graph import builder

load_dotenv()


def initial_state(invoice_id: str) -> dict:
    return {"invoice_id": invoice_id, "decision": "", "status": "new"}


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: python main.py start|status|resume <invoice_id> [approved|rejected]")
        sys.exit(1)

    command = sys.argv[1]
    invoice_id = sys.argv[2]
    config = {"configurable": {"thread_id": invoice_id}}
    url = os.environ["DATABASE_URL"]

    with PostgresSaver.from_conn_string(url) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        if command == "start":
            result = graph.invoke(initial_state(invoice_id), config)
            for intr in result.get("__interrupt__", []):
                print("PAUSED FOR APPROVAL:")
                print(intr.value)

        elif command == "status":
            snapshot = graph.get_state(config)
            print("next node:", snapshot.next)
            print("state:", snapshot.values)

        elif command == "resume":
            decision = sys.argv[3] if len(sys.argv) > 3 else "approved"
            result = graph.invoke(Command(resume=decision), config)
            print("final state:", result)

        else:
            print(f"unknown command: {command}")
            sys.exit(1)


if __name__ == "__main__":
    main()