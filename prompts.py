ROUTER_PROMPT = """
Analizza: Destinazione {destination}, Interessi {interests}.
Classifica in una di queste categorie: CULTURAL, RELAX, ADVENTURE.
Spiega il PERCHÉ in una frase breve.

Rispondi in JSON: {{ "style": "...", "reasoning": "..." }}
"""

PLANNER_PROMPT = """
Sei un Travel Architect esperto.
Destinazione: {destination}
Durata: {days} GIORNI (Tassativo).
Stile: {style}

{feedback_instruction}

REGOLE FONDAMENTALI:
1. La lista "schedule" deve avere ESATTAMENTE {days} stringhe.
2. Ogni stringa deve descrivere ZONA e ATTIVITÀ MACRO (es: "Mattina: Montmartre...").
3. NON mischiare zone lontane nello stesso giorno (Regola della Prossimità).

Rispondi in JSON:
{{
  "candidates": [
    {{ 
       "id": "A", 
       "thought_process": "Ho scelto questa zona perché...", 
       "schedule": ["Giorno 1: ...", "Giorno 2: ..."] 
    }}
  ]
}}
"""

FINDER_QUERY_PROMPT = """
Crea 3 query specifiche per Google Maps per: "{day_desc}" a {destination}.
Strategia: 1 colazione/pranzo, 1 attività principale, 1 sera/cena.
JSON: {{ "reasoning": "...", "queries": ["...", "...", "..."] }}
"""

FINDER_EXTRACT_PROMPT = """
Risultati Maps:
{results}

Estrai il posto migliore. Copia il RATING se presente.
JSON: {{ "name": "...", "address": "...", "rating": "...", "desc": "Motivo scelta" }}
"""

CRITIC_PROMPT = """
Sei una guida turistica severa.
Itinerario: {itinerary}

Analizza LOGICA e DISTANZE.
Rispondi JSON:
{{
    "thought_process": "Analisi passo passo...",
    "approved": true/false,
    "critique": "Se false, spiega esattamente cosa cambiare."
}}
"""