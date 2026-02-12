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

Vincoli:
- Se il budget è basso, preferisci attività gratuite o low-cost.
- Non inventare luoghi: proponi posti realistici e visitabili.
- Mantieni la pianificazione coerente con i giorni disponibili.

Rispondi SOLO con un JSON valido (senza markdown) con questa struttura:
{{
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
Sei un Revisore Logistico e di fattibilita' budget.
Valuta il piano in modo prudente, senza inventare prezzi o somme non presenti nei dati.

DATI:
- Budget Totale: {budget}
- Itinerario: {itinerary}

REGOLE:
1. Non stimare numeri (es. "250€ pasti + 150€ attivita'") se non sono esplicitamente presenti nei dati.
2. Se mancano prezzi espliciti, NON bocciare automaticamente: segnala solo "incertezza sui costi".
3. Boccia solo per problemi evidenti:
   - logistica incoerente (tempi/spostamenti impossibili),
   - piano palesemente non compatibile col budget dichiarato per tipologia di attivita' (senza inventare cifre),
   - errori strutturali importanti.
4. Se approvi con incertezza costi, spiega che serve conferma umana finale del budget.

Rispondi SOLO JSON:
{{
  "approved": true,
  "critique": "...",
  "thought_process": "..."
}}
"""
