import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

url = os.environ["DATABASE_URL"]

with PostgresSaver.from_conn_string(url) as checkpointer:
    checkpointer.setup()

print("checkpointer tables created")