import json
import re
import os 
from langchain_core.messages import HumanMessage
from state import TravelAgentState
from model import llm
from tools import find_places_on_maps
from logger import logger
import urllib.parse

# --- HELPER ROBUSTO ---
def extract_json(text):
    text = text.strip()
    # Pulizia Markdown
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()

# --- 1. INIT NODE ---
def init_node(state: TravelAgentState):
    logger.log_event("INIT", "START", "Nuova sessione")
    dest = state.get("destination") or input("\n 🌍 Dove vuoi andare? ").strip()
    days = state.get("days") or input(" 📅 Quanti giorni? ").strip()
    interests = state.get("interests") or input(" 🎨 Interessi? ").strip()
    
    # Conversione sicura a intero
    try:
        days_int = int(days)
    except:
        days_int = 3
        
    return {"destination": dest, "days": days_int, "interests": interests}

# --- 2. ROUTER NODE ---
def travel_router_node(state: TravelAgentState):
    logger.log_event("ROUTER", "START", "Analisi Stile")
    
    prompt = f"""
    Analizza: Destinazione {state['destination']}, Interessi {state['interests']}.
    Classifica in: CULTURAL, RELAX, ADVENTURE.
    Spiega il PERCHÉ in una frase breve.
    
    JSON: {{ "style": "...", "reasoning": "..." }}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(extract_json(response.content), strict=False)
        style = data.get("style", "RELAX")
        # VISIBILITÀ PENSIERO
        logger.log_event("ROUTER", "THOUGHT", data.get("reasoning", "Nessun pensiero"))
    except:
        style = "RELAX"
        
    logger.log_event("ROUTER", "RESULT", f"Stile: {style}")
    return {"travel_style": style}

# --- 3. PLANNER NODE (Verbose Fix) ---
def trip_planner_node(state: TravelAgentState):
    logger.log_event("PLANNER", "START", "Pianificazione Itinerario")
    
    dest = state['destination']
    days = state['days']
    style = state['travel_style']
    feedback = state.get("feedback")
    
    # Logica differenziata: Se c'è un errore, sii chirurgico. Se è nuovo, sii creativo.
    if feedback:
        logger.log_event("PLANNER", "THOUGHT", f"⚠️ Devo correggere il piano precedente. Critica ricevuta: {feedback}")
        instruction_mode = f"""
        MODALITÀ: CORREZIONE CRITICA.
        Il piano precedente è stato bocciato.
        Motivo bocciatura: "{feedback}"
        
        Genera UN SOLO piano corretto (Opzione A) che risolva questi problemi.
        Non generare B o C. Concentrati sulla qualità di A.
        """
    else:
        instruction_mode = f"""
        MODALITÀ: CREAZIONE (Tree of Thoughts).
        Genera 3 opzioni diverse (A, B, C) basate sullo stile {style}.
        """

    prompt = f"""
    Sei un Travel Architect.
    Destinazione: {dest}
    Durata: {days} GIORNI (Tassativo).
    
    {instruction_mode}
    
    REGOLE FONDAMENTALI:
    1. La lista "schedule" deve avere ESATTAMENTE {days} stringhe. Una per giorno.
    2. Ogni stringa deve descrivere ZONA e ATTIVITÀ MACRO (es: "Mattina: Montmartre, Pom: Le Marais").
    3. NON mischiare zone lontane nello stesso giorno.
    
    Rispondi JSON:
    {{
      "candidates": [
        {{ 
           "id": "A", 
           "thought_process": "Ho scelto questa zona perché...", 
           "schedule": ["Giorno 1: ...", "Giorno 2: ..."] 
        }},
        ... (altri se richiesti)
      ]
    }}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Parsing robusto
    candidates = []
    try:
        raw_json = extract_json(response.content)
        data = json.loads(raw_json, strict=False)
        candidates = data.get("candidates", [])
    except Exception as e:
        logger.log_event("PLANNER", "ERROR", f"Errore JSON Planner: {e}")
    
    # Se fallisce o lista vuota, Fallback intelligente
    if not candidates:
        fallback_plan = [f"Giorno {i+1}: Centro storico e attrazioni principali" for i in range(days)]
        candidates = [{"id": "Fallback", "thought_process": "Errore generazione, uso default.", "schedule": fallback_plan}]

    # Selezione (o conferma se è correzione)
    selected = candidates[0] # Di default prendiamo il primo
    
    # Se avevamo più opzioni (modalità creazione), facciamo scegliere l'LLM
    if not feedback and len(candidates) > 1:
        # Qui potremmo fare un secondo step di valutazione, ma per verbosità stampiamo le opzioni
        logger.log_event("PLANNER", "THOUGHT", f"Ho generato {len(candidates)} opzioni.")
        for c in candidates:
             print(f"      🔹 Opzione {c['id']}: {c['thought_process'][:100]}...")
    
    # VISIBILITÀ PENSIERO
    logger.log_event("PLANNER", "THOUGHT", f"Scelto piano {selected['id']}: {selected.get('thought_process', 'N/A')}")
    
    # Force Check Giorni
    final_sched = selected['schedule']
    if len(final_sched) > days:
        logger.log_event("PLANNER", "WARNING", f"Taglio giorni extra ({len(final_sched)} -> {days})")
        final_sched = final_sched[:days]
    elif len(final_sched) < days:
        # Riempitivo
        while len(final_sched) < days:
             final_sched.append("Giorno Extra: Relax e Shopping libero")

    return {"draft_schedule": final_sched, "retry_count": state.get("retry_count", 0) + 1}

# --- 4. FINDER NODE (Correzione Rating) ---
def places_finder_node(state: TravelAgentState):
    logger.log_event("FINDER", "START", "Ricerca su Maps")
    
    draft = state['draft_schedule']
    dest = state['destination']
    final_itinerary = []
    
    for i, day_desc in enumerate(draft, 1):
        logger.log_event("FINDER", "THOUGHT", f"Analisi Giorno {i}: '{day_desc}'")
        
        # 1. Creazione Query
        prompt_query = f"""
        Crea 3 query specifiche per Google Maps per:
        "{day_desc}" a {dest}.
        JSON: {{ "reasoning": "...", "queries": ["...", "...", "..."] }}
        """
        resp = llm.invoke([HumanMessage(content=prompt_query)])
        try:
            q_data = json.loads(extract_json(resp.content), strict=False)
            queries = q_data.get("queries", [])
            logger.log_event("FINDER", "THOUGHT", f"Strategia: {q_data.get('reasoning')}")
        except:
            queries = [f"Ristoranti {dest}", f"Musei {dest}"]

        day_places = []
        for q in queries:
            logger.log_event("FINDER", "ACTION", f"Cerco: '{q}'")
            results = find_places_on_maps.invoke(q)
            
            # 2. Estrazione (QUI ERA L'ERRORE)
            prompt_extract = f"""
            Risultati Maps per '{q}':
            {results}
            
            Estrai il posto migliore.
            IMPORTANTE: Copia il RATING (es. "4.5/5") se presente.
            
            JSON: {{ 
                "name": "...", 
                "address": "...", 
                "rating": "...",  
                "desc": "Motivo scelta" 
            }}
            """
            try:
                r_place = llm.invoke([HumanMessage(content=prompt_extract)])
                p_data = json.loads(extract_json(r_place.content), strict=False)
                
                # Fallback se l'LLM dimentica ancora il rating
                if "rating" not in p_data:
                    p_data["rating"] = "N/A"
                    
                day_places.append(p_data)
            except:
                pass

        final_itinerary.append({
            "day_number": i,
            "focus": day_desc,
            "places": day_places
        })
        
    return {"itinerary": final_itinerary}

# --- 5. CRITIC NODE (Verbose) ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione")
    itinerary = state['itinerary']
    
    prompt = f"""
    Sei una guida severa.
    Itinerario: {json.dumps(itinerary, indent=2)}
    
    Analizza LOGICA e DISTANZE.
    
    Rispondi JSON:
    {{
        "thought_process": "Analisi passo passo...",
        "approved": true/false,
        "critique": "Se false, spiega esattamente cosa togliere o cambiare."
    }}
    """
    resp = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        data = json.loads(extract_json(resp.content), strict=False)
    except:
        data = {"approved": True, "thought_process": "Errore tecnico critico, approvazione forzata."}
    
    # VISIBILITÀ
    logger.log_event("CRITIC", "THOUGHT", data.get("thought_process", "Nessun pensiero"))
    
    if data.get('approved'):
        logger.log_event("CRITIC", "RESULT", "✅ Approvato")
        return {"is_approved": True}
    else:
        logger.log_event("CRITIC", "WARNING", f"❌ Bocciato: {data.get('critique')}")
        return {"is_approved": False, "feedback": data.get('critique')}

# --- 6. PUBLISHER NODE: HYBRID (Chat + HTML) ---
def publisher_node(state: TravelAgentState):
    dest = state['destination']
    days = state['days']
    filename = f"viaggio_{dest.replace(' ', '_')}.html"
    
    # ---------------------------------------------------------
    # 1. SETUP INIZIALE (HTML Header + Terminal Header)
    # ---------------------------------------------------------
    
    # Header Terminale
    print("\n" + "="*60)
    print(f"✈️  ITINERARIO FINALE: {dest.upper()}")
    print("="*60)

    # Header HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Viaggio a {dest}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f4f7f6; color: #333; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            .day-card {{ background: #fff; border: 1px solid #e1e1e1; margin-bottom: 25px; border-radius: 10px; overflow: hidden; }}
            .day-header {{ background: #3498db; color: white; padding: 15px; font-size: 1.3em; font-weight: bold; }}
            .place-list {{ list-style: none; padding: 0; margin: 0; }}
            .place-item {{ padding: 20px; border-bottom: 1px solid #eee; display: flex; align-items: start; }}
            .icon {{ font-size: 1.8em; margin-right: 15px; min-width: 40px; }}
            .place-name {{ font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-bottom: 5px; }}
            .rating {{ color: #f1c40f; font-size: 0.9em; margin-left: 5px; }}
            .addr {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 5px; }}
            .desc {{ color: #555; line-height: 1.4; }}
            .map-btn {{ display: block; background: #27ae60; color: white; text-align: center; padding: 15px; text-decoration: none; font-weight: bold; transition: 0.3s; }}
            .map-btn:hover {{ background: #219150; }}
            .footer {{ text-align: center; margin-top: 40px; color: #aaa; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✈️ {dest.upper()} ({days} Giorni)</h1>
            <p style="text-align:center">Stile: <b>{state['travel_style']}</b> | Interessi: {state['interests']}</p>
    """

    # ---------------------------------------------------------
    # 2. CICLO UNICO (Processa Dati -> Stampa -> Scrive HTML)
    # ---------------------------------------------------------
    for day in state['itinerary']:
        day_title = f"Giorno {day['day_number']}: {day['focus']}"
        
        # A. Output Terminale
        print(f"\n📅 {day_title}")
        print("-" * 40)
        
        # B. Output HTML
        html_content += f"""
            <div class="day-card">
                <div class="day-header">📅 {day_title}</div>
                <ul class="place-list">
        """
        
        route_stops = []
        
        for p in day['places']:
            # Estrazione dati sicura
            name = p.get('name', 'Posto sconosciuto')
            address = p.get('address', '')
            rating = p.get('rating', 'N/A')
            desc = p.get('desc', '')
            
            # Icona logica per HTML
            icon = "📍"
            if "ristorante" in name.lower() or "caffè" in name.lower(): icon = "🍽️"
            elif "museo" in name.lower() or "galleria" in name.lower(): icon = "🏛️"
            elif "parco" in name.lower() or "giardino" in name.lower(): icon = "🌳"
            
            # --- STAMPA TERMINALE ---
            print(f"   📍 {name} (⭐ {rating})")
            print(f"      🏠 {address}")
            print(f"      📝 {desc}")
            print("      ---")
            
            # --- SCRITTURA HTML ---
            html_content += f"""
                <li class="place-item">
                    <span class="icon">{icon}</span>
                    <div>
                        <div class="place-name">{name} <span class="rating">⭐ {rating}</span></div>
                        <div class="addr">🏠 {address}</div>
                        <div class="desc">📝 {desc}</div>
                    </div>
                </li>
            """
            
            # Raccolta tappe per Maps
            target = address if address else name
            if target:
                route_stops.append(urllib.parse.quote(target))
        
        html_content += "</ul>"
        
        # --- GENERAZIONE LINK MAPS (Per entrambi) ---
        if route_stops:
            map_url = "https://www.google.com/maps/dir/" + "/".join(route_stops)
            
            # Link nel Terminale
            print(f"   🗺️  Link Maps: {map_url}")
            
            # Bottone nell'HTML
            html_content += f"""
                <a href="{map_url}" target="_blank" class="map-btn">
                    🗺️ VEDI ITINERARIO SU GOOGLE MAPS
                </a>
            """
            
        html_content += "</div>" # Chiude day-card

    # ---------------------------------------------------------
    # 3. CHIUSURA E SALVATAGGIO
    # ---------------------------------------------------------
    html_content += f"""
            <div class="footer">Generato da AI Travel Architect • {state['travel_style']} Edition</div>
        </div>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("\n" + "="*60)
    print(f"💾 FILE SALVATO: {filename}")
    print("="*60)
    
    return {}