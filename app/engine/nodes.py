import os
import json
from colorama import Fore, Style, init
from langchain_core.messages import HumanMessage
from app.core.state import TravelAgentState
from app.core.model import llm
from app.tools.maps import find_places_on_maps
from app.core.logger import logger
from app.core.utils import safe_json_parse
from app.engine import prompts

init(autoreset=True)

# --- 1. INIT NODE ---
def init_node(state: TravelAgentState):
    logger.log_event("INIT", "START", "Nuova sessione")
    
    print(Fore.CYAN + "\n🌍 TRAVEL AGENT AI 2.0 - ARCHITECT EDITION\n")
    
    dest = input(f"{Fore.GREEN}📍 Dove vuoi andare? {Style.RESET_ALL}").strip()
    days = input(f"{Fore.GREEN}📅 Quanti giorni? {Style.RESET_ALL}").strip()
    interests = input(f"{Fore.GREEN}🎨 Interessi? {Style.RESET_ALL}").strip()
    budget = input(f"{Fore.GREEN}💰 Budget? (Low/Medio/Lusso) {Style.RESET_ALL}").strip() or "Medio"
    companion = input(f"{Fore.GREEN}👥 Con chi viaggi? (Solo/Coppia/Famiglia) {Style.RESET_ALL}").strip() or "Solo"
    
    logger.info(f"Input: {dest}, {days}gg, {budget}, {companion}")

    return {
        "user_input": f"{days} giorni a {dest}, interessi: {interests}. Budget: {budget}, Gruppo: {companion}",
        "destination": dest,
        "days": days,
        "interests": interests,
        "budget": budget,
        "companion": companion,
        "retry_count": 0,
        "is_approved": False,
        "itinerary": [],
        "critic_feedback": None
    }

# --- 2. ROUTER NODE ---
def travel_router_node(state: TravelAgentState):
    logger.log_event("ROUTER", "START", "Analisi Stile")
    formatted_prompt = prompts.ROUTER_PROMPT.format(user_input=state['user_input'])
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content, default_value={"style": "RELAX"})
    logger.log_event("ROUTER", "THOUGHT", data.get("reasoning", "N/A"))
    return {"travel_style": data.get("style", "RELAX")}

# --- 3. PLANNER NODE (RIFATTO) ---
def trip_planner_node(state: TravelAgentState):
    logger.log_event("PLANNER", "START", "Pianificazione Itinerario")
    
    feedback = state.get("critic_feedback") # Nota: critic_feedback coerente con lo state
    feedback_instr = ""
    if feedback:
        logger.log_event("PLANNER", "WARNING", f"Feedback Critic: {feedback}")
        feedback_instr = f"CORREGGI L'ITINERARIO PRECEDENTE BASANDOTI SU QUESTO ERRORE: {feedback}"

    budget = state.get('budget', 'Medio')
    companion = state.get('companion', 'Solo')
    
    formatted_prompt = prompts.PLANNER_PROMPT.format(
        destination=state['destination'],
        days=state['days'],
        style=state['travel_style'],
        budget=budget,
        companion=companion,
        feedback_instruction=feedback_instr
    )
    
    # Chiamata LLM
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # Parsing Diretto dell'Itinerario
    itinerary_data = safe_json_parse(response.content)
    
    if not itinerary_data or not isinstance(itinerary_data, list):
        logger.log_event("PLANNER", "ERROR", "JSON non valido, uso fallback.")

        itinerary_data = [{"day_number": 1, "focus": "Esplorazione", "places": [{"name": f"Centro {state['destination']}", "address": ""}]}]

    logger.log_event("PLANNER", "THOUGHT", f"Generata bozza con {len(itinerary_data)} giorni.")
    
    return {"itinerary": itinerary_data, "retry_count": state.get("retry_count", 0) + 1}

# --- 4. FINDER NODE (RIFATTO) ---
def places_finder_node(state: TravelAgentState):
    """
    Non chiede più all'LLM di generare query.
    Prende i nomi dei luoghi dal JSON del Planner e cerca su Maps.
    """
    logger.log_event("FINDER", "START", "Verifica Luoghi Reali su Maps")
    
    updated_itinerary = []
    
    # Itera sui giorni pianificati dal Planner
    for day in state.get('itinerary', []):
        logger.log_event("FINDER", "THOUGHT", f"Processo Giorno {day.get('day_number')}")
        
        validated_places = []
        for place in day.get('places', []):
            place_name = place.get('name', 'Luogo sconosciuto')
            
            # Costruiamo la query di ricerca
            query = f"{place_name} {state['destination']}"
            
            logger.log_event("FINDER", "ACTION", f"Cerco: {query}")
            
            results = find_places_on_maps.invoke(query)

            if results and isinstance(results, list) and len(results) > 0:
                # Usiamo i dati reali di Google
                real_place = results[0]
                validated_places.append({
                    "name": real_place.get("name"),
                    "address": real_place.get("address"),
                    "rating": real_place.get("rating", "N/A"),
                    "description": f"Verificato su Maps (ID: {real_place.get('place_id')})"
                })
            else:
                # Non trovato, teniamo il dato del Planner ma lo segniamo
                logger.log_event("FINDER", "WARNING", f"Non trovato su Maps: {place_name}")
                validated_places.append({
                    "name": place_name,
                    "address": place.get("address", "Indirizzo non trovato"),
                    "rating": "N/A",
                    "description": "Luogo suggerito dall'AI (non verificato)"
                })
        
        # Aggiorniamo i luoghi del giorno
        day['places'] = validated_places
        updated_itinerary.append(day)
        
    return {"itinerary": updated_itinerary}

# --- 5. CRITIC NODE ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione Logistica")
    
    formatted_prompt = prompts.CRITIC_PROMPT.format(
        destination=state['destination'],
        itinerary=json.dumps(state['itinerary'], indent=2)
    )
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content, default_value={"approved": True})
    
    if data.get('approved'):
        logger.log_event("CRITIC", "RESULT", "✅ Approvato")
        return {"is_approved": True, "critic_feedback": None}
    else:
        logger.log_event("CRITIC", "WARNING", f"❌ Bocciato: {data.get('critique')}")
        return {"is_approved": False, "critic_feedback": data.get('critique')}

# --- 6. PUBLISHER NODE ---
def publisher_node(state: TravelAgentState):
    from app.tools.publisher import generate_html_report, print_terminal_report, generate_docx_report

    print_terminal_report(state)
    html_file = generate_html_report(state)
    docx_file = generate_docx_report(state)

    print("\n" + "="*60)
    print(f"\n📄 Report salvati in 'outputs/': \n   - {os.path.basename(html_file)}\n   - {os.path.basename(docx_file)}")
    print("="*60)
    return state