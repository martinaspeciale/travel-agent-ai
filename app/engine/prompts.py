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

AUTOTEST DI AFFIDABILITÀ:
Valuta la logistica e la coerenza delle tue scelte. 
Assegna un punteggio di confidenza (confidence_score) da 0.0 a 1.0. 
Se non sei sicuro della logistica o dei luoghi per questa specifica destinazione, abbassa il punteggio.

Rispondi SOLO con un JSON valido (senza markdown) con questa struttura:
{{
  "confidence_score": 0.85,
  "itinerary": [
    {{
      "day_number": 1,
      "focus": "Tema del giorno",
      "places": [
        {{ "name": "Nome Luogo 1", "address": "Indirizzo" }}
      ]
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
Analizza questo itinerario per {destination}:
{itinerary}

Verifica logistica, distanze e coerenza (es. non mandare un utente Low Cost in un ristorante a 3 stelle Michelin).
Rispondi SOLO JSON:
{{
  "approved": true/false,
  "critique": "Motivo del rifiuto (sii specifico)"
}}
"""