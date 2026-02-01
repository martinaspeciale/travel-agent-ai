import json
import re

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
    

    