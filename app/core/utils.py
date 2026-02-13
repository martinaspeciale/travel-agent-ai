import json
import os
import re
import sys
import time
import random

def extract_json(text: str) -> str:
    """
    Pulisce l'output dell'LLM per estrarre solo il JSON valido.
    Rimuove i blocchi markdown ```json ... ```.
    """
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()

def safe_json_parse(json_str: str, default_value=None):
    """
    Tenta di parsare il JSON in modo robusto.
    Restituisce default_value in caso di errore.
    """
    if default_value is None:
        default_value = {}
        
    try:
        clean_str = extract_json(json_str)
        # strict=False aiuta a gestire caratteri di controllo illegali
        return json.loads(clean_str, strict=False)
    except Exception:
        return default_value
    


def extract_budget_number(budget_str: str) -> float:
    """
    Estrae il budget gestendo milioni, k, e formati testuali.
    Esempio: '1 milione' -> 1000000.0, '50k' -> 50000.0
    """
    clean_str = budget_str.lower().replace(',', '').strip()
    
    # Mappatura moltiplicatori
    multipliers = {
        'k': 1000,
        'mila': 1000,
        'milion': 1000000, # prende 'milione' e 'milioni'
        'm': 1000000
    }
    
    # Estrae il numero (anche decimale es. 1.5 milioni)
    match = re.search(r"(\d+\.?\d*)", clean_str)
    if not match:
        return 50.0 if 'low' in clean_str else 999999.0

    number = float(match.group(1))

    # Applica il moltiplicatore corretto
    for word, value in multipliers.items():
        if word in clean_str:
            number *= value
            break # Evita di moltiplicare due volte (es. 'm' è in 'milione')
            
    return number


def typing_print(text, speed=0.003):
    """Stampa il testo con un effetto 'typing' live."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Aggiungiamo variabilità per renderlo più 'umano'
        time.sleep(speed + random.uniform(0, 0.005))
    print() # Va a capo alla fine


def format_terminal_link(label: str, url: str) -> str:
    """
    Restituisce un hyperlink cliccabile in terminali compatibili con OSC 8.
    Fallback: URL testuale per massima compatibilita'.
    """
    if not url:
        return label

    # Se non siamo su un terminale interattivo, evitiamo sequenze ANSI.
    if not sys.stdout.isatty():
        return f"{label}: {url}"

    term = os.getenv("TERM", "")
    if term.lower() == "dumb":
        return f"{label}: {url}"

    # https://iterm2.com/documentation-escape-codes.html
    osc8 = f"\033]8;;{url}\033\\{label}\033]8;;\033\\"
    # Mantiene sempre anche l'URL testuale per terminali/IDE che non supportano OSC 8.
    return f"{osc8} ({url})"
