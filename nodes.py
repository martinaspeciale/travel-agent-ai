import json
from langchain_core.messages import HumanMessage
from state import TravelAgentState
from model import llm
from tools import find_places_on_maps
from logger import logger

def extract_json(text):
    text = text.strip()
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
    try: days_int = int(days)
    except: days_int = 3
    return {"destination": dest, "days": days_int, "interests": interests}

# --- 2. ROUTER NODE ---
def travel_router_node(state: TravelAgentState):
    logger.log_event("ROUTER", "START", "Analisi Stile")
    prompt = f"Analizza: {state['destination']}, {state['interests']}. Classifica: CULTURAL, RELAX, ADVENTURE. JSON: {{'style': '...', 'reasoning': '...'}}"
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(extract_json(response.content))
        style = data.get("style", "RELAX")
        logger.log_event("ROUTER", "THOUGHT", data.get("reasoning"))
    except: style = "RELAX"
    return {"travel_style": style}

# --- 3. PLANNER NODE (ToT) ---
def trip_planner_node(state: TravelAgentState):
    logger.log_event("PLANNER", "START", "Pianificazione (ToT)")
    dest, days, style = state['destination'], state['days'], state['travel_style']
    feedback = state.get("feedback")

    mode = "CREAZIONE" if not feedback else f"CORREZIONE (Critica: {feedback})"
    prompt = f"""
    Sei un Travel Planner. Destinazione: {dest}, Giorni: {days}, Stile: {style}.
    Modalità: {mode}.
    Genera un piano giornaliero. Rispetta ESATTAMENTE {days} giorni.
    JSON: {{ "candidates": [ {{ "id": "A", "schedule": ["Giorno 1: ...", "Giorno 2: ..."] }} ] }}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(extract_json(response.content))
        schedule = data["candidates"][0]["schedule"][:days] # Force cut
    except:
        schedule = [f"Giorno {i+1}: Esplorazione centro" for i in range(days)]

    return {"draft_schedule": schedule, "retry_count": state.get("retry_count", 0) + 1}

# --- 4. FINDER NODE ---
def places_finder_node(state: TravelAgentState):
    logger.log_event("FINDER", "START", "Ricerca Luoghi")
    itinerary = []
    for i, focus in enumerate(state['draft_schedule'], 1):
        # Semplificazione per il commit intermedio
        logger.log_event("FINDER", "ACTION", f"Cerco per: {focus}")
        res = find_places_on_maps.invoke(f"Posti per {focus} a {state['destination']}")
        # Mock parsing veloce
        itinerary.append({"day_number": i, "focus": focus, "places": [{"name": "Place Placeholder", "address": "Center", "rating": "4.5/5", "desc": res[:50]}]})
    return {"itinerary": itinerary}

# --- 5. CRITIC NODE ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione")
    # Logica dummy per il primo pass
    return {"is_approved": True}

# --- 6. PUBLISHER NODE (BASE - Solo testo) ---
def publisher_node(state: TravelAgentState):
    print("\n=== ITINERARIO GENERATO ===")
    for day in state['itinerary']:
        print(f"Giorno {day['day_number']}: {day['focus']}")
    return {}