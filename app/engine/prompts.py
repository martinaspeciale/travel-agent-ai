ROUTER_PROMPT = """
Analizza la richiesta di viaggio seguente:
"{user_input}"

Il tuo compito è determinare lo "Stile di Viaggio" più adatto.
Scegli UNO tra: "RELAX", "AVVENTURA", "CULTURALE", "GASTRONOMICO", "LUSSO", "LOW COST".

Rispondi in JSON:
{{
  "reasoning": "Spiegazione breve...",
  "style": "STILE_SCELTO"
}}
"""

PLANNER_PROMPT = """
Sei un Travel Planner esperto. Crea un itinerario dettagliato per {destination} di {days} giorni.

PROFILO:
- Stile: {style}
- Budget: {budget} (Scegli ristoranti/attività coerenti con questo budget)
- Gruppo: {companion} (Adatta i ritmi per questo tipo di gruppo)

{feedback_instruction}

ISTRUZIONI OUTPUT:
Non fare liste puntate generiche. Genera una struttura JSON precisa.
Per ogni giorno, elenca 2-3 luoghi specifici (nomi precisi di musei, ristoranti, parchi).

Rispondi SOLO con un JSON valido (senza markdown) che segua questa struttura esatta:
[
  {{
    "day_number": 1,
    "focus": "Tema del giorno (es. Arte e Storia)",
    "places": [
      {{ "name": "Nome Luogo 1", "address": "Zona o Indirizzo approssimativo" }},
      {{ "name": "Nome Ristorante X", "address": "Zona centro" }}
    ]
  }},
  {{
    "day_number": 2,
    "focus": "...",
    "places": [...]
  }}
]
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
Analizza questo itinerario per {destination}:
{itinerary}

Verifica logistica, distanze e coerenza (es. non mandare un utente Low Cost in un ristorante a 3 stelle Michelin).
Rispondi SOLO JSON:
{{
  "approved": true/false,
  "critique": "Motivo del rifiuto (sii specifico)"
}}
"""