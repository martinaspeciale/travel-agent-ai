import json
import os
import re
import sys
import time
import random

def extract_json(text: str) -> str:
    """
    Clean LLM output and extract valid JSON content only.
    Removes markdown blocks like ```json ... ```.
    """
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()

def safe_json_parse(json_str: str, default_value=None):
    """
    Parse JSON robustly.
    Return default_value on any parsing error.
    """
    if default_value is None:
        default_value = {}
        
    try:
        clean_str = extract_json(json_str)
        # strict=False helps with illegal control characters.
        return json.loads(clean_str, strict=False)
    except Exception:
        return default_value
    


def extract_budget_number(budget_str: str) -> float:
    """
    Extract budget value handling millions, k-suffixes, and text formats.
    Example: '1 milione' -> 1000000.0, '50k' -> 50000.0
    """
    clean_str = budget_str.lower().replace(',', '').strip()
    
    # Multiplier mapping.
    multipliers = {
        'k': 1000,
        'mila': 1000,
        'milion': 1000000,  # Matches both 'milione' and 'milioni'.
        'm': 1000000
    }
    
    # Extract numeric value (including decimals like 1.5).
    match = re.search(r"(\d+\.?\d*)", clean_str)
    if not match:
        return 50.0 if 'low' in clean_str else 999999.0

    number = float(match.group(1))

    # Apply the matching multiplier.
    for word, value in multipliers.items():
        if word in clean_str:
            number *= value
            break  # Prevent double multiplication (e.g. 'm' inside 'milione').
            
    return number


def typing_print(text, speed=0.003):
    """Print text with a live typing effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        # Add slight variability for a more natural typing effect.
        time.sleep(speed + random.uniform(0, 0.005))
    print()  # New line at the end.


def format_terminal_link(label: str, url: str) -> str:
    """
    Return a clickable hyperlink for OSC 8-compatible terminals.
    Fallback to plain text URL for maximum compatibility.
    """
    if not url:
        return label

    # Avoid ANSI sequences in non-interactive terminals.
    if not sys.stdout.isatty():
        return f"{label}: {url}"

    term = os.getenv("TERM", "")
    if term.lower() == "dumb":
        return f"{label}: {url}"

    # https://iterm2.com/documentation-escape-codes.html
    osc8 = f"\033]8;;{url}\033\\{label}\033]8;;\033\\"
    # Keep plain URL text for terminals/IDEs without OSC 8 support.
    return f"{osc8} ({url})"
