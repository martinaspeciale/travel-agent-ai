import datetime
from termcolor import colored

class AgentLogger:
    def log_event(self, agent_name, event_type, content, metadata=None):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        prefix = f"[{timestamp}] --- {agent_name} ---"
        
        if event_type == "START":
            print(colored(f"\n{prefix}", "green", attrs=["bold"]))
            print(colored(f"   ► {content}", "white", attrs=["bold"]))
        elif event_type == "THOUGHT":
            print(colored(f"   🧠 [Pensiero] {content}", "cyan"))
        elif event_type == "ACTION":
            print(colored(f"   🛠️ [Tool] {content}", "yellow"))
        elif event_type == "RESULT":
            print(colored(f"   ✅ [Risultato] {content}", "blue"))
        elif event_type == "WARNING":
            print(colored(f"   ⚠️ [Warning] {content}", "magenta"))
        elif event_type == "ERROR":
            print(colored(f"   ❌ [Errore] {content}", "red"))
        else:
            print(f"   {content}")

# Istanza globale
logger = AgentLogger()