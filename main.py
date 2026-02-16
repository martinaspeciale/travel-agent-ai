import sys
import os

# Add the current travel-agent-ai/ folder to Python's import path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph import app as workflow_app

if __name__ == "__main__":
    print("🤖 TRAVEL AGENT AI ARCHITECT")
    # Run the graph.
    workflow_app.invoke({"retry_count": 0, "is_approved": False})
