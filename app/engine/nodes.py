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
from app.core.utils import extract_budget_number
from app.tools.search import search_prices_tool

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
    logger.log_event("PLANNER", "START", "Pianificazione con Autovalutazione")
    
    if state.get("critic_feedback"):
        # Iniettiamo un comando di "Cambio Rotta"
        feedback = f"\n[!] ATTENZIONE: Il piano precedente è stato BOCCIATO. Non riproporre le stesse attrazioni. Cambia tipologia di luoghi."

    feedback = state.get("critic_feedback")
    feedback_instr = ""
    if feedback:
        logger.log_event("PLANNER", "WARNING", f"Feedback Critic: {feedback}")
        feedback_instr = f"CORREGGI L'ITINERARIO PRECEDENTE BASANDOTI SU QUESTO ERRORE: {feedback}"

    formatted_prompt = prompts.PLANNER_PROMPT.format(
        destination=state['destination'],
        days=state['days'],
        style=state['travel_style'],
        budget=state.get('budget', 'Medio'),
        companion=state.get('companion', 'Solo'),
        feedback_instruction=feedback_instr
    )
    
    # Chiamata LLM
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # Parsing del nuovo formato JSON (che ora include confidence_score e itinerary)
    data = safe_json_parse(response.content)
    
    # Estrazione sicura dei dati
    itinerary_data = data.get("itinerary", [])
    confidence = data.get("confidence_score", 0.0)
    
    logger.log_event("PLANNER", "INFO", f"Confidenza Agente: {confidence}")

    # --- IMPLEMENTAZIONE HITL ---
    # Se la confidenza è < 0.7, forziamo il blocco dell'approvazione automatica
    is_low_confidence = confidence < 0.7
    
    if is_low_confidence:
        logger.log_event("PLANNER", "WARNING", f"⚠️ Confidenza Bassa ({confidence}). Richiesta revisione manuale.")
        # Impostiamo un feedback che il Critic o l'interfaccia useranno per fermare il flusso
        confidence_feedback = f"REVISIONE RICHIESTA: L'agente ha una confidenza di solo {confidence}."
        existing_feedback = state.get("critic_feedback")
        if existing_feedback:
            status_feedback = f"{existing_feedback} | {confidence_feedback}"
        else:
            status_feedback = confidence_feedback
    else:
        status_feedback = state.get("critic_feedback")

    # Fallback se il JSON è malformato
    if not itinerary_data or not isinstance(itinerary_data, list):
        logger.log_event("PLANNER", "ERROR", "JSON non valido, uso fallback.")
        itinerary_data = [{"day_number": 1, "focus": "Esplorazione", "places": [{"name": f"Centro {state['destination']}", "address": ""}]}]

    return {
        "itinerary": itinerary_data, 
        "confidence_score": confidence,          # Salviamo lo score nello stato
        "is_approved": not is_low_confidence,    # Se la confidenza è bassa, NON è approvato
        "critic_feedback": status_feedback,
        "retry_count": state.get("retry_count", 0) + 1
    }

# --- 4. FINDER NODE ---
def places_finder_node(state: TravelAgentState):
    logger.log_event("FINDER", "START", "Verifica Luoghi con Tool Maps")
    
    total_budget = extract_budget_number(state['budget'])
    num_days = int(state['days']) if state['days'].isdigit() else 1
    daily_budget = total_budget / num_days

    # Contesto budget/costi basato sui luoghi reali dell'itinerario
    budget_context_lines = []
    if daily_budget < 70:
        logger.log_event("FINDER", "WARNING", f"Budget critico rilevato: {daily_budget}€/giorno. Uso Tavily.")
        # Usiamo Tavily per trovare opzioni gratuite nella destinazione
        logger.log_tool("TAVILY", f"Ricerca attività low-cost a {state['destination']}...")
        query = f"free things to do and cheap eats in {state['destination']}"
        budget_context_lines.append(search_prices_tool(query))

    updated_itinerary = []
    
    for day in state.get('itinerary', []):
        validated_places = []
        for place in day.get('places', []):
            place_name = place.get('name', 'Luogo sconosciuto')
            query = f"{place_name} {state['destination']}"
            
            logger.log_event("FINDER", "ACTION", f"Richiesta Tool per: {query}")
            
            # --- CHIAMATA TRAMITE DECORATORE TOOL ---
            try:
                # Essendo un @tool, usiamo .invoke()
                results = find_places_on_maps.invoke(query)
            except Exception as e:
                logger.log_event("FINDER", "ERROR", f"Errore invoke tool: {e}")
                results = []

            # Se il tool ha restituito la lista di dict correttamente
            if results and isinstance(results, list) and len(results) > 0:
                real_place = results[0]
                cost_info = search_prices_tool(f"{real_place.get('name')} {state['destination']}")
                if cost_info:
                    budget_context_lines.append(f"{real_place.get('name')}: {cost_info}")
                validated_places.append({
                    "name": real_place.get("name"),
                    "address": real_place.get("address"),
                    "rating": real_place.get("rating", "N/A"),
                    "description": "Verificato con Google Maps",
                    "cost_info": cost_info
                })
                logger.log_event("FINDER", "RESULT", f"Trovato: {real_place.get('name')}")
            else:
                logger.log_event("FINDER", "WARNING", f"Nessun match per: {place_name}")
                cost_info = search_prices_tool(f"{place_name} {state['destination']}")
                if cost_info:
                    budget_context_lines.append(f"{place_name}: {cost_info}")
                validated_places.append({
                    "name": place_name,
                    "address": place.get("address", "N/A"),
                    "rating": "N/A",
                    "description": "Non verificato (Verifica quota API)",
                    "cost_info": cost_info
                })
        
        day['places'] = validated_places
        updated_itinerary.append(day)
        
    budget_context = "\n".join([line for line in budget_context_lines if line])
    return {"budget_context": budget_context, "itinerary": updated_itinerary}

# --- 5. CRITIC NODE ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione Logistica")
    
    formatted_prompt = prompts.CRITIC_PROMPT.format(
        destination=state['destination'],
        itinerary=json.dumps(state['itinerary'], indent=2),
        budget=state.get('budget', 'Non specificato'),                  
        budget_context=state.get('budget_context', 'Nessun dato extra')
    )
    
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    data = safe_json_parse(response.content, default_value={"approved": True})
    
    if data.get('approved'):
        # Usiamo 'RESULT' per il successo (+)
        logger.log_event("CRITIC", "RESULT", "[+] Approvato: L'itinerario rispetta i vincoli logistici e di budget.")
        return {"is_approved": True, "critic_feedback": None}
    else:
        # Usiamo 'ERROR' o 'WARNING' per la bocciatura [!]
        logger.log_event("CRITIC", "ERROR", f"[!] Bocciato: {data.get('critique')}")
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

def ask_human_node(state: TravelAgentState):
    logger.log_event("SYSTEM", "WARNING", f"CONFIDENZA BASSA ({state.get('confidence_score')})")
    print(Fore.YELLOW + "\n⚠️  L'AI non è sicura dell'itinerario generato.")
    scelta = input(Fore.WHITE + "Vuoi procedere comunque? (s/n): ").lower().strip()
    
    if scelta == 's':
        return {"is_approved": True, "critic_feedback": None}
    else:
        motivo = input("Cosa non va? Lascia un feedback per l'AI: ")
        return {"is_approved": False, "critic_feedback": motivo, "retry_count": state.get("retry_count", 0) + 1}
    

def failure_handler_node(state: TravelAgentState):
    logger.log_event("SYSTEM", "ERROR", "[!] FATAL: Impossibile riconciliare i vincoli dopo vari tentativi.")
    
    # Costruiamo un messaggio di spiegazione basato sull'ultimo feedback del Critic
    failure_msg = (
        "L'agente non è riuscito a generare un itinerario che soddisfi "
        f"sia il budget che la logistica. Ultimo feedback: {state.get('critic_feedback')}"
    )
    
    # Creiamo un itinerario 'vuoto' per non far crashare il Publisher
    return {
        "itinerary": [], 
        "is_approved": False, 
        "critic_feedback": failure_msg
    }
