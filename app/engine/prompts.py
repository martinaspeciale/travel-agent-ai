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
Se ricevi un budget context con prezzi alti, ignora i luoghi famosi a pagamento e cerca solo 'free walking tours' e 'street food'.
Se non sei sicuro della logistica o dei luoghi per questa specifica destinazione, abbassa il punteggio.

Se il budget è palesemente insufficiente per la destinazione (es. 30€ per 3gg a Venezia), 
imposta confidence_score a 0.3 e scrivi nel focus che l'itinerario è puramente simbolico o gratuito.

Se la destinazione fornita dall'utente è generica (es. 'un posto al caldo', 'luogo esotico'), 
DEVI impostare confidence_score < 0.5. 
Non scegliere una destinazione a caso. 
Il sistema deve fermarsi e chiedere: 'Quale luogo esotico preferisci? (es. Bali, Maldive, Caraibi)'

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
