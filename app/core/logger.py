import os
import re
import sys
import uuid
import time
import random
import inspect
import shutil
from datetime import datetime
from colorama import Fore, Style, init
from app.core.utils import typing_print

# Inizializza colorama
init(autoreset=True)

class TravelLogger:
    def __init__(self):
        # --- Componenti di Tracing ---
        self.trace_id = str(uuid.uuid4())[:8]  # Trace ID unico per la sessione
        self.node_start_time = time.time()     # Timer per calcolare la latenza (Span)
        
        self.LOG_DIR = "logs"
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)
        
        self.session_file = os.path.join(
            self.LOG_DIR, 
            f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        )
        
        # Colori Originali
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
TRAVEL AGENT AI ARCHITECT - SESSIONE AVVIATA
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Log File: {self.session_file}
Trace ID: {self.trace_id}
{'='*60}
"""
        with open(self.session_file, "w", encoding="utf-8") as f:
            f.write(header + "\n")

    def _calculate_latency(self):
        """Calcola i ms passati dall'ultimo evento (Attributes - Slide 18)"""
        now = time.time()
        latency_ms = int((now - self.node_start_time) * 1000)
        self.node_start_time = now
        return latency_ms

    def _strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _pad_after_prefix(self, prefix, target_col=20):
        visible_len = len(self._strip_ansi(prefix))
        pad_len = max(1, target_col - visible_len)
        return " " * pad_len

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

    # --- Metodi Smart (Emoji rimosse) ---
    def info(self, msg): self._log("*", msg)
    def error(self, msg): self._log("!", msg, Fore.RED)
    def warning(self, msg): self._log("!", msg, Fore.YELLOW)
    def thought(self, msg): self._log("?", f"[Pensiero] {msg}")
    def action(self, msg): self._log("#", f"[Tool] {msg}")

    def _log(self, level_icon, msg, color_override=None):
        latency = self._calculate_latency()
        timestamp = datetime.now().strftime("%H:%M:%S")
        node_name, node_color = self._get_caller_info()
        
        if color_override:
            node_color = color_override

        # Output leggibile con header allineato rispetto al trace
        prefix = f"{Style.DIM}[{latency}ms]{Style.RESET_ALL} "
        tab_pad = self._pad_after_prefix(prefix)
        header_text = f"[{timestamp}] --- {node_name} ---"
        print(f"{prefix}{tab_pad}{node_color}{header_text}{Style.RESET_ALL}")
        print(f"{tab_pad}{level_icon} {msg}{Style.RESET_ALL}\n")
        
        self._write(f"[{timestamp}] --- {node_name} --- {latency}ms --- {level_icon} {msg}")

    # --- Metodo Legacy ---
    def log_event(self, node_name, event_type, message):
        latency = self._calculate_latency()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "ROUTER": Fore.GREEN, "PLANNER": Fore.CYAN, 
            "FINDER": Style.BRIGHT + Fore.GREEN, "CRITIC": Fore.YELLOW, 
            "PUBLISHER": Fore.GREEN, "ERROR": Fore.RED, "INIT": Style.DIM + Fore.GREEN,
            "TAVILY": Fore.MAGENTA, "TAVILY_FLIGHTS": Style.BRIGHT + Fore.MAGENTA,
            "SERPAPI_FLIGHTS": Style.BRIGHT + Fore.CYAN
        }
        color = colors.get(node_name, Fore.GREEN)
        
        icons = {
            "THOUGHT": "[?]", "ACTION": "==>", "INFO": " * ", 
            "ERROR": "[!]", "RESULT": "[+]", "START": ">>>"
        }
        icon = icons.get(event_type, " - ")
        
        prefix = f"{Style.DIM}[{latency}ms]{Style.RESET_ALL} "
        tab_pad = self._pad_after_prefix(prefix)
        header_text = f"[{timestamp}] {node_name} {icon} [{event_type}]"
        print(f"{prefix}{tab_pad}{color}{header_text}{Style.RESET_ALL}")
        
        for char in message:
            sys.stdout.write(char)
            sys.stdout.flush()
            delay = 0.01 if event_type == "THOUGHT" else 0.004
            time.sleep(delay + random.uniform(0, 0.01))
        
        print(f"{Style.RESET_ALL}")
        self._write(f"[{timestamp}] --- {node_name} --- {latency}ms --- {icon} [{event_type}] {message}")

    def log_tool(self, tool_name, action_desc):
        latency = self._calculate_latency()
        timestamp = datetime.now().strftime("%H:%M:%S")
        tool_name_upper = (tool_name or "").upper()
        if "TAVILY" in tool_name_upper:
            color = Fore.MAGENTA
        elif "SERPAPI" in tool_name_upper:
            color = Fore.CYAN
        else:
            color = Fore.BLUE
        
        prefix = f"{Style.DIM}[{latency}ms]{Style.RESET_ALL} "
        tab_pad = self._pad_after_prefix(prefix)
        header_text = f"[{timestamp}] TOOL [{tool_name}] ==> "
        print(f"{prefix}{tab_pad}{color}{header_text}{Style.RESET_ALL}")
        
        typing_print(action_desc, speed=0.01)
        self._write(f"[{timestamp}] TOOL [{tool_name}] --- {latency}ms --- {action_desc}")

logger = TravelLogger()
