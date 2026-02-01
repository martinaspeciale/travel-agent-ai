import sys
import os

# Aggiungiamo la cartella corrente travel-agent-ai/ al percorso di ricerca di Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph import app as workflow_app

if __name__ == "__main__":
    print("🤖 TRAVEL AGENT AI ARCHITECT")
    # Lancia il grafo
    workflow_app.invoke({"retry_count": 0, "is_approved": False})