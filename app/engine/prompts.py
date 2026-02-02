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
Sei il Supervisore della Qualità (Pillar: Robustness & Safety).
Analizza l'itinerario per {destination} considerando questi vincoli:

BUDGET UTENTE: {budget}
DATI REALI SUI COSTI (Grounding): {budget_context}

COMPITI:
1. Verifica se i luoghi suggeriti sono compatibili con il budget.
2. Se i dati reali (Tavily) indicano prezzi alti per un'attrazione e il budget è basso, BOCCIA l'itinerario.
3. Suggerisci alternative gratuite se necessario.

Rispondi SOLO JSON:
{{
  "approved": true/false,
  "critique": "Spiegazione basata sui costi reali",
  "thought_process": "Ragionamento sul rapporto budget/costi"
}}
"""