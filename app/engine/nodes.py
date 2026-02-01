import urllib.parse
from langchain_core.messages import HumanMessage
from app.core.state import TravelAgentState
from app.core.model import llm
from app.tools.maps import find_places_on_maps
from app.core.logger import logger
from app.core.utils import safe_json_parse, extract_json
from app.engine import prompts

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
    
    formatted_prompt = prompts.ROUTER_PROMPT.format(
        destination=state['destination'], 
        interests=state['interests']
    )
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content, default_value={"style": "RELAX"})
    
    logger.log_event("ROUTER", "THOUGHT", data.get("reasoning", "N/A"))
    return {"travel_style": data.get("style", "RELAX")}

# --- 3. PLANNER NODE ---
def trip_planner_node(state: TravelAgentState):
    logger.log_event("PLANNER", "START", "Pianificazione Itinerario")
    
    feedback = state.get("feedback")
    feedback_instr = ""
    if feedback:
        logger.log_event("PLANNER", "WARNING", f"Correzione richiesta: {feedback}")
        feedback_instr = f"MODALITÀ CORREZIONE. Il piano precedente è stato bocciato: {feedback}. Correggi gli errori."

    formatted_prompt = prompts.PLANNER_PROMPT.format(
        destination=state['destination'],
        days=state['days'],
        style=state['travel_style'],
        feedback_instruction=feedback_instr
    )
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content)
    
    candidates = data.get("candidates", [])
    if not candidates:
        # Fallback
        schedule = [f"Giorno {i+1}: Esplorazione centro" for i in range(state['days'])]
        selected = {"thought_process": "Fallback attivo", "schedule": schedule}
    else:
        selected = candidates[0]

    logger.log_event("PLANNER", "THOUGHT", selected.get("thought_process", "N/A"))
    
    # Taglio o estensione giorni per sicurezza
    final_sched = selected['schedule'][:state['days']]
    
    return {"draft_schedule": final_sched, "retry_count": state.get("retry_count", 0) + 1}

# --- 4. FINDER NODE ---
def places_finder_node(state: TravelAgentState):
    logger.log_event("FINDER", "START", "Ricerca su Maps")
    final_itinerary = []
    
    for i, day_desc in enumerate(state['draft_schedule'], 1):
        # 1. Genera Query
        q_prompt = prompts.FINDER_QUERY_PROMPT.format(day_desc=day_desc, destination=state['destination'])
        q_resp = llm.invoke([HumanMessage(content=q_prompt)])
        q_data = safe_json_parse(q_resp.content, default_value={"queries": [f"Attrazioni {state['destination']}"]})
        
        logger.log_event("FINDER", "THOUGHT", f"Giorno {i}: {q_data.get('reasoning', 'Generazione query')}")
        
        day_places = []
        for q in q_data.get("queries", []):
            logger.log_event("FINDER", "ACTION", f"Cerco: '{q}'")
            results = find_places_on_maps.invoke(q)
            
            # 2. Estrai Dati
            e_prompt = prompts.FINDER_EXTRACT_PROMPT.format(results=results)
            e_resp = llm.invoke([HumanMessage(content=e_prompt)])
            place_data = safe_json_parse(e_resp.content)
            
            if place_data:
                if isinstance(place_data, list):
                    # Se l'LLM ha risposto con una lista (es. [place1, place2]), li aggiungiamo tutti
                    day_places.extend(place_data)
                elif isinstance(place_data, dict):
                    # Se è un oggetto singolo --> append
                    day_places.append(place_data)


        final_itinerary.append({"day_number": i, "focus": day_desc, "places": day_places})
        
    return {"itinerary": final_itinerary}

# --- 5. CRITIC NODE ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione Logistica")
    
    # Passiamo una versione ridotta dell'itinerario per risparmiare token se necessario
    formatted_prompt = prompts.CRITIC_PROMPT.format(itinerary=state['itinerary'])
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content, default_value={"approved": True})
    
    logger.log_event("CRITIC", "THOUGHT", data.get("thought_process", "N/A"))
    
    if data.get('approved'):
        logger.log_event("CRITIC", "RESULT", "✅ Approvato")
        return {"is_approved": True}
    else:
        logger.log_event("CRITIC", "WARNING", f"❌ Bocciato: {data.get('critique')}")
        return {"is_approved": False, "feedback": data.get('critique')}

# --- 6. PUBLISHER NODE ---
def publisher_node(state: TravelAgentState):
    from app.tools.publisher import generate_html_report, print_terminal_report, generate_docx_report

    # 1. Stampa in chat
    print_terminal_report(state)
    
    # 2. Genera HTML
    html_file = generate_html_report(state)

    # 3. Genera WORD
    docx_file = generate_docx_report(state)

    print("\n" + "="*60)
    print(f"\n📄 Report salvati: \n   - {html_file}\n   - {docx_file}")
    print("="*60)
    return state