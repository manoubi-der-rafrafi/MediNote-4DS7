"""
Medinote interactive chat — run with: python chat.py
"""
import sys, logging
logging.basicConfig(level=logging.WARNING)

from orchestrator import OrchestratorAgent

print("Medinote CRM — AI Assistant")
print("Type your question in French or English. Type 'quit' to exit.\n")

try:
    orch = OrchestratorAgent()
except Exception as e:
    print(f"ERROR: Could not start orchestrator: {e}")
    sys.exit(1)

while True:
    try:
        req = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        break

    if not req:
        continue
    if req.lower() in ("quit", "exit", "q"):
        print("Goodbye.")
        break

    try:
        result = orch.run(req)
    except KeyboardInterrupt:
        print("\n[Query interrupted. Type your next question.]\n")
        continue
    except Exception as e:
        print(f"[ERROR: {e}]\n")
        continue

orch.close()
