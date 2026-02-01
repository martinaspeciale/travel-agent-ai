import os
import re
import inspect
from datetime import datetime
from colorama import Fore, Style, init

# Inizializza colorama
init(autoreset=True)

class TravelLogger:
    def __init__(self):
        self.LOG_DIR = "logs"
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)
        
        self.session_file = os.path.join(
            self.LOG_DIR, 
            f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        )
        
        # Colori
        self.NODE_COLORS = {
            "router_node": Fore.MAGENTA,
            "trip_planner_node": Fore.CYAN,
            "finder_node": Fore.BLUE,
            "critic_node": Fore.YELLOW,
            "publisher_node": Fore.GREEN,
            "find_places_on_maps": Fore.BLUE,
            "init_node": Fore.WHITE
        }
        
        self.NODE_NAMES = {
            "router_node": "ROUTER",
            "trip_planner_node": "PLANNER",
            "finder_node": "FINDER",
            "critic_node": "CRITIC",
            "publisher_node": "PUBLISHER",
            "find_places_on_maps": "TOOL",
            "init_node": "INIT"
        }

        self._init_log_file()

    def _init_log_file(self):
        header = f"""
{'='*60}
🤖 TRAVEL AGENT AI ARCHITECT - SESSIONE AVVIATA
📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📂 Log File: {self.session_file}
{'='*60}
"""
        with open(self.session_file, "w", encoding="utf-8") as f:
            f.write(header + "\n")

    def _strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _write(self, content):
        clean_content = self._strip_ansi(content)
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(clean_content + "\n")

    def _get_caller_info(self):
        stack = inspect.stack()
        for frame in stack:
            func_name = frame.function
            if func_name in self.NODE_NAMES:
                return self.NODE_NAMES[func_name], self.NODE_COLORS[func_name]
        return "SYSTEM", Fore.WHITE

    # --- Metodi Smart ---
    def info(self, msg): self._log("►", msg)
    def error(self, msg): self._log("⚠️", msg, Fore.RED)
    def warning(self, msg): self._log("⚠️", msg, Fore.YELLOW)
    def thought(self, msg): self._log("🧠", f"[Pensiero] {msg}")
    def action(self, msg): self._log("🛠️", f"[Tool] {msg}")

    def _log(self, level_icon, msg, color_override=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        node_name, node_color = self._get_caller_info()
        
        if color_override:
            node_color = color_override

        # Output Terminale (TUTTO COLORATO)
        # Il colore inizia prima dell'header e finisce DOPO il messaggio
        full_text = f"{node_color}[{timestamp}] --- {node_name} ---\n   {level_icon} {msg}{Style.RESET_ALL}"
        print(f"{full_text}\n")
        
        # Output File
        self._write(f"[{timestamp}] --- {node_name} ---\n   {level_icon} {msg}")

    # --- Metodo Legacy (Tutto colorato) ---
    def log_event(self, node_name, event_type, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "ROUTER": Fore.MAGENTA, "PLANNER": Fore.CYAN, 
            "FINDER": Fore.BLUE, "CRITIC": Fore.YELLOW, 
            "PUBLISHER": Fore.GREEN, "ERROR": Fore.RED,
            "INIT": Fore.WHITE
        }
        color = colors.get(node_name, Fore.WHITE)
        
        icons = {
            "THOUGHT": "🧠", "ACTION": "🛠️", "INFO": "►", 
            "ERROR": "⚠️", "RESULT": "✅", "START": "🚦"
        }
        icon = icons.get(event_type, "•")
        
        # Stampa TUTTO colorato
        full_text = f"{color}[{timestamp}] --- {node_name} ---\n   {icon} [{event_type}] {message}{Style.RESET_ALL}"
        
        print(f"{full_text}\n")
        self._write(f"[{timestamp}] --- {node_name} ---\n   {icon} [{event_type}] {message}")

logger = TravelLogger()
