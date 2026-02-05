import os
import json
import re
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
    
    print(Fore.CYAN + "\n::: TRAVEL AGENT AI 2.0 - ARCHITECT EDITION :::\n")
    
    dest = input(f"{Fore.GREEN}>> Dove vuoi andare? {Style.RESET_ALL}").strip()
    days = input(f"{Fore.GREEN}>> Quanti giorni? {Style.RESET_ALL}").strip()
    interests = input(f"{Fore.GREEN}>> Interessi? {Style.RESET_ALL}").strip()
    budget_total = input(f"{Fore.GREEN}>> Budget totale indicativo (€)? {Style.RESET_ALL}").strip()
    companion = input(f"{Fore.GREEN}>> Con chi viaggi? (Solo/Coppia/Famiglia) {Style.RESET_ALL}").strip() or "Solo"
    
    logger.info(f"Input: {dest}, {days}gg, {budget_total or 'N/D'}€, {companion}")

    budget_note = f"Budget totale: {budget_total}€." if budget_total else "Budget non specificato."

    return {
        "user_input": f"{days} giorni a {dest}, interessi: {interests}. {budget_note} Gruppo: {companion}",
        "destination": dest,
        "days": days,
        "interests": interests,
        "budget": f"{budget_total}€" if budget_total else "",
        "budget_total": budget_total or None,
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

    # Blacklist luoghi già proposti se il piano è stato bocciato
    banned_places = []
    if state.get("critic_feedback") and state.get("itinerary"):
        for day in state.get("itinerary", []):
            for place in day.get("places", []):
                name = place.get("name")
                if name:
                    banned_places.append(name)
        if banned_places:
            banned_list = ", ".join(sorted(set(banned_places)))
            feedback_instr = f"{feedback_instr}\nNON USARE QUESTI LUOGHI: {banned_list}."

    budget_total = state.get("budget_total")
    total_budget = extract_budget_number(str(budget_total)) if budget_total else extract_budget_number(state.get("budget", ""))
    num_days = int(state['days']) if state['days'].isdigit() else 1
    daily_budget = total_budget / num_days
    if daily_budget < 60:
        low_cost_instr = (
            "BUDGET BASSO: proponi solo street food, mercati, free tour e luoghi gratuiti. "
            "Evita ristoranti costosi o attività a pagamento."
        )
        feedback_instr = f"{feedback_instr}\n{low_cost_instr}" if feedback_instr else low_cost_instr

    budget_total = state.get("budget_total")
    budget_label = f"{budget_total}€ totale (indicativo)" if budget_total else state.get('budget', 'Non specificato')

    formatted_prompt = prompts.PLANNER_PROMPT.format(
        destination=state['destination'],
        days=state['days'],
        style=state['travel_style'],
        budget=budget_label,
        companion=state.get('companion', 'Solo'),
        feedback_instruction=feedback_instr
    )
    
    # Chiamata LLM
    response = llm.invoke([HumanMessage(content=formatted_prompt)])
    
    # Parsing del nuovo formato JSON (che ora include confidence_score e itinerary)
    data = safe_json_parse(response.content)
    
    # Estrazione sicura dei dati
    itinerary_data = data.get("itinerary", [])

    # Stampa sintetica dell'itinerario proposto
    if itinerary_data and isinstance(itinerary_data, list):
        print("\nItinerario proposto:")
        for day in itinerary_data:
            day_number = day.get("day_number", "?")
            focus = day.get("focus", "N/A")
            places = day.get("places", [])
            place_names = ", ".join([p.get("name", "Luogo") for p in places]) if places else "Nessun luogo"
            print(f"- Giorno {day_number}: {focus} | {place_names}")

    status_feedback = state.get("critic_feedback")

    # Fallback se il JSON è malformato
    if not itinerary_data or not isinstance(itinerary_data, list):
        logger.log_event("PLANNER", "ERROR", "JSON non valido, uso fallback.")
        itinerary_data = [{"day_number": 1, "focus": "Esplorazione", "places": [{"name": f"Centro {state['destination']}", "address": ""}]}]

    return {
        "itinerary": itinerary_data, 
        "confidence_score": state.get("confidence_score", 0.0),
        "is_approved": False,
        "critic_feedback": status_feedback,
        "retry_count": state.get("retry_count", 0) + 1,
        "banned_places": sorted(set(banned_places)) if banned_places else state.get("banned_places")
    }

# --- 4. FINDER NODE ---
def places_finder_node(state: TravelAgentState):
    logger.log_event("FINDER", "START", "Verifica Luoghi con Tool Maps")
    
    budget_total = state.get("budget_total")
    if budget_total:
        total_budget = extract_budget_number(str(budget_total))
    else:
        total_budget = extract_budget_number(state['budget'])
    num_days = int(state['days']) if state['days'].isdigit() else 1
    daily_budget = total_budget / num_days

    # Contesto budget/costi basato sui luoghi reali dell'itinerario
    budget_context_lines = []
    tavily_calls = 0
    max_tavily_calls = 2

    def _maybe_tavily(query: str):
        nonlocal tavily_calls
        if tavily_calls >= max_tavily_calls:
            return None
        tavily_calls += 1
        return search_prices_tool(query)

    def _summarize_cost_info(cost_info: dict) -> str:
        if not cost_info:
            return "n/d"
        summary = cost_info.get("summary", "").strip()
        if not summary:
            return "n/d"
        lines = [line.strip(" -") for line in summary.splitlines() if line.strip()]
        first = lines[0] if lines else summary
        first = re.sub(r"\([^)]*https?://[^)]*\)", "", first)
        first = re.sub(r"https?://\S+", "", first).strip()
        if len(first) > 140:
            first = first[:137] + "..."
        return first if first else "n/d"

    def _address_matches_destination(address: str, destination: str) -> bool:
        if not address or not destination:
            return False
        address_l = address.lower()
        dest_l = destination.lower()
        if dest_l in address_l:
            return True
        aliases = {
            "milano": "milan",
            "roma": "rome",
            "firenze": "florence",
            "venezia": "venice",
            "napoli": "naples",
            "torino": "turin"
        }
        alt = aliases.get(dest_l)
        return alt in address_l if alt else False

    if daily_budget < 70:
        logger.log_event("FINDER", "WARNING", f"Budget critico rilevato: {daily_budget}€/giorno. Uso Tavily.")
        # Usiamo Tavily per trovare opzioni gratuite nella destinazione
        logger.log_tool("TAVILY", f"Ricerca attività low-cost a {state['destination']}...")
        query = f"free things to do and cheap eats in {state['destination']}"
        low_cost_info = _maybe_tavily(query)
        if low_cost_info:
            budget_context_lines.append(low_cost_info)

    updated_itinerary = []
    
    for day in state.get('itinerary', []):
        validated_places = []
        day_print_lines = []
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
                if not _address_matches_destination(real_place.get("address", ""), state["destination"]):
                    logger.log_event("FINDER", "WARNING", f"Luogo fuori destinazione: {real_place.get('name')}")
                    results = []
                
            if results and isinstance(results, list) and len(results) > 0:
                real_place = results[0]
                cost_text = _maybe_tavily(f"{real_place.get('name')} {state['destination']}")
                cost_info = None
                if cost_text:
                    cost_info = {
                        "source": "tavily",
                        "summary": cost_text
                    }
                    budget_context_lines.append(f"{real_place.get('name')}: {cost_text}")
                validated_places.append({
                    "name": real_place.get("name"),
                    "address": real_place.get("address"),
                    "rating": real_place.get("rating", "N/A"),
                    "description": "Verificato con Google Maps",
                    "cost_info": cost_info
                })
                logger.log_event("FINDER", "RESULT", f"Trovato: {real_place.get('name')}")
                day_print_lines.append(
                    f"{real_place.get('name')} | {real_place.get('address')} | rating: {real_place.get('rating', 'N/A')} | costi: {_summarize_cost_info(cost_info)}"
                )
            else:
                logger.log_event("FINDER", "WARNING", f"Nessun match per: {place_name}")
                cost_info = None
                validated_places.append({
                    "name": place_name,
                    "address": place.get("address", "N/A"),
                    "rating": "N/A",
                    "description": "Non verificato (Verifica quota API)",
                    "cost_info": cost_info
                })
                day_print_lines.append(
                    f"{place_name} | {place.get('address', 'N/A')} | rating: N/A | costi: {_summarize_cost_info(cost_info)}"
                )
        
        day['places'] = validated_places
        updated_itinerary.append(day)

        if day_print_lines:
            print(f"\nLuoghi selezionati (giorno {day.get('day_number', '?')}):")
            for line in day_print_lines:
                print(f"- {line}")
        
    budget_context = "\n".join([line for line in budget_context_lines if line])
    return {"budget_context": budget_context, "itinerary": updated_itinerary}

# --- 5. CONFIDENCE NODE (POST-FINDER) ---
def confidence_evaluator_node(state: TravelAgentState):
    logger.log_event("CONFIDENCE", "START", "Valutazione confidenza post-verifica")

    itinerary = state.get("itinerary", [])
    if not itinerary:
        confidence = 0.0
    else:
        confidence = 0.8

        unverified = 0
        total_places = 0
        missing_costs = 0

        for day in itinerary:
            for place in day.get("places", []):
                total_places += 1
                if place.get("description", "").startswith("Non verificato"):
                    unverified += 1
                if not place.get("cost_info"):
                    missing_costs += 1

        if total_places > 0:
            unverified_ratio = unverified / total_places
            missing_cost_ratio = missing_costs / total_places
            confidence -= 0.4 * unverified_ratio
            confidence -= 0.3 * missing_cost_ratio

        budget_total = state.get("budget_total")
        total_budget = extract_budget_number(str(budget_total)) if budget_total else extract_budget_number(state.get("budget", ""))
        num_days = int(state['days']) if state['days'].isdigit() else 1
        daily_budget = total_budget / num_days
        if daily_budget < 60:
            confidence -= 0.1

    confidence = max(0.0, min(1.0, round(confidence, 2)))
    logger.log_event("CONFIDENCE", "INFO", f"Confidenza Agente: {confidence}")

    if confidence < 0.7:
        logger.log_event("CONFIDENCE", "WARNING", f"Confidenza bassa ({confidence}). Richiesta revisione manuale.")

    return {"confidence_score": confidence}

# --- 5. CRITIC NODE ---
def logistics_critic_node(state: TravelAgentState):
    logger.log_event("CRITIC", "START", "Validazione Logistica")
    
    budget_total = state.get("budget_total")
    budget_label = f"{budget_total}€ totale (indicativo)" if budget_total else state.get('budget', 'Non specificato')

    formatted_prompt = prompts.CRITIC_PROMPT.format(
        destination=state['destination'],
        itinerary=json.dumps(state['itinerary'], indent=2),
        budget=budget_label,                  
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
    print(f"\nReport salvati in 'outputs/': \n   - {os.path.basename(html_file)}\n   - {os.path.basename(docx_file)}")
    print("="*60)
    return state

def ask_human_node(state: TravelAgentState):
    logger.log_event("SYSTEM", "WARNING", f"CONFIDENZA BASSA ({state.get('confidence_score')})")
    print(Fore.YELLOW + "\nATTENZIONE: l'AI non e' sicura dell'itinerario generato.")
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
