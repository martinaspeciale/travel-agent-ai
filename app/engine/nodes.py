import os
import json
import re
from datetime import datetime
from colorama import Fore, Style, init
from langchain_core.messages import HumanMessage
from app.core.state import TravelAgentState
from app.core.model import llm
from app.tools.maps import find_places_on_maps
from app.core.logger import logger
from app.core.utils import safe_json_parse
from app.engine import prompts
from app.core.utils import extract_budget_number
from app.tools.search import search_flights_tool

init(autoreset=True)


def _parse_flexible_date(raw_text: str):
    text = (raw_text or "").strip()
    if not text:
        return None

    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        pass

    month_map = {
        "gennaio": 1, "january": 1,
        "febbraio": 2, "february": 2,
        "marzo": 3, "march": 3,
        "aprile": 4, "april": 4,
        "maggio": 5, "may": 5,
        "giugno": 6, "june": 6,
        "luglio": 7, "july": 7,
        "agosto": 8, "august": 8,
        "settembre": 9, "september": 9,
        "ottobre": 10, "october": 10,
        "novembre": 11, "november": 11,
        "dicembre": 12, "december": 12,
    }
    m = re.match(r"^\s*(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s*$", text, flags=re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month_key = m.group(2).strip().lower()
        month = month_map.get(month_key)
        if month:
            year = datetime.today().year
            try:
                parsed = datetime(year, month, day).date()
                if parsed < datetime.today().date():
                    parsed = datetime(year + 1, month, day).date()
                return parsed
            except ValueError:
                return None
    return None

# --- 1. INIT NODE ---
def init_node(state: TravelAgentState):
    logger.log_event("INIT", "START", "Nuova sessione")
    
    print(Fore.CYAN + "\n::: TRAVEL AGENT AI 2.0 - ARCHITECT EDITION :::\n")
    
    dest = input(f"{Fore.GREEN}>> Dove vuoi andare? {Style.RESET_ALL}").strip()
    interests = input(f"{Fore.GREEN}>> Interessi? {Style.RESET_ALL}").strip()
    budget_total = input(f"{Fore.GREEN}>> Budget totale indicativo (€)? {Style.RESET_ALL}").strip()
    companion = input(f"{Fore.GREEN}>> Con chi viaggi? (Solo/Coppia/Famiglia) {Style.RESET_ALL}").strip() or "Solo"
    origin = input(f"{Fore.GREEN}>> Partenza volo (citta, opzionale)? {Style.RESET_ALL}").strip()
    depart_date = input(f"{Fore.GREEN}>> Data andata (YYYY-MM-DD, obbligatoria)? {Style.RESET_ALL}").strip()
    while not depart_date:
        logger.log_event("INIT", "WARNING", "Data andata mancante: richiesta obbligatoria.")
        depart_date = input(f"{Fore.GREEN}>> Inserisci la data andata (YYYY-MM-DD): {Style.RESET_ALL}").strip()
    return_date = input(f"{Fore.GREEN}>> Data ritorno (YYYY-MM-DD, opzionale)? {Style.RESET_ALL}").strip()

    days = ""
    if depart_date and return_date:
        d1 = _parse_flexible_date(depart_date)
        d2 = _parse_flexible_date(return_date)
        if d1 and d2:
            delta = (d2 - d1).days + 1
            if delta > 0:
                days = str(delta)
                logger.log_event("INIT", "INFO", f"Giorni calcolati automaticamente dalle date: {days}")

    if not days:
        days = "3"
        logger.log_event(
            "INIT",
            "WARNING",
            "Date non sufficienti/valide per calcolare i giorni: uso fallback 3 giorni."
        )
    
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
        "origin": origin or None,
        "depart_date": depart_date or None,
        "return_date": return_date or None,
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


# --- 2b. FLIGHT SEARCH NODE (minimal wiring) ---
def flight_search_node(state: TravelAgentState):
    def _extract_price_value(*chunks):
        text = " ".join([(c or "") for c in chunks])
        patterns = [
            r"€\s*([0-9]+(?:[.,][0-9]{1,2})?)",
            r"([0-9]+(?:[.,][0-9]{1,2})?)\s*€",
            r"\$\s*([0-9]+(?:[.,][0-9]{1,2})?)",
            r"\bPrice\s*([0-9]+(?:[.,][0-9]{1,2})?)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(",", ".")
                try:
                    return float(value)
                except ValueError:
                    return None
        return None

    def _extract_time_value(*chunks):
        text = " ".join([(c or "") for c in chunks])
        match = re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", text)
        if match:
            return match.group(0)
        return "n/d"

    def _enrich_rows(rows, date_value):
        enriched = []
        for row in rows:
            title = row.get("title", "")
            content = row.get("content", "")
            raw_content = row.get("raw_content", "")
            price_value = row.get("price_value")
            if price_value is None:
                price_value = _extract_price_value(title, content, raw_content)
            depart_time = _extract_time_value(title, content, raw_content)
            enriched.append({
                **row,
                "price_value": price_value,
                "depart_date": date_value or "n/d",
                "depart_time": depart_time,
            })
        return sorted(
            enriched,
            key=lambda r: r["price_value"] if r.get("price_value") is not None else float("inf")
        )

    origin = (state.get("origin") or "").strip()
    destination = (state.get("destination") or "").strip()
    depart_date = (state.get("depart_date") or "").strip()
    return_date = (state.get("return_date") or "").strip()

    # Keep this step non-blocking: if key flight inputs are missing, continue normally.
    if not origin or not destination:
        logger.log_event("FLIGHTS", "SKIP", "Origin or destination missing, skipping flight search.")
        return {
            "flight_options": [],
            "flight_summary": "Flight search skipped: missing origin or destination.",
            "flight_confidence_score": 0.0,
        }

    current_depart_date = depart_date
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        logger.log_event(
            "FLIGHTS",
            "START",
            f"Search flights {origin} -> {destination} (depart: {current_depart_date or 'N/D'})"
        )

        rows = search_flights_tool(
            origin=origin,
            destination=destination,
            depart_date=current_depart_date,
            return_date=return_date,
        )

        if not rows:
            logger.log_event("FLIGHTS", "WARNING", "Nessuna opzione volo trovata.")
            change = input(
                Fore.WHITE + "Nessun volo trovato. Vuoi cambiare data andata? (s/n): "
            ).strip().lower()
            if change == "s":
                new_date = input("Nuova data andata (YYYY-MM-DD): ").strip()
                while not new_date:
                    logger.log_event("FLIGHTS", "WARNING", "Data andata mancante: richiesta obbligatoria.")
                    new_date = input("Inserisci la nuova data andata (YYYY-MM-DD): ").strip()
                current_depart_date = new_date
                continue
            return {
                "flight_options": [],
                "flight_summary": "No flight options found from configured sources.",
                "flight_confidence_score": 0.0,
                "depart_date": current_depart_date or None,
            }

        sorted_rows = _enrich_rows(rows, current_depart_date)
        best = sorted_rows[0]
        best_return = None

        best_price = (
            f"{best.get('price_value'):.2f}" if best.get("price_value") is not None else "n/d"
        )
        logger.log_event(
            "FLIGHTS",
            "RESULT",
            f"Proposta volo: {best.get('title', 'N/D')} | prezzo stimato: {best_price}"
        )
        print("\nProposta volo piu' economica trovata:")
        print(f"- {best.get('title', 'N/D')}")
        print(f"- Data partenza: {best.get('depart_date', 'n/d')}")
        print(f"- Orario partenza: {best.get('depart_time', 'n/d')}")
        if best.get("url"):
            print(f"- Link: {best.get('url')}")

        if return_date:
            logger.log_event(
                "FLIGHTS",
                "START",
                f"Search return flight {destination} -> {origin} (depart: {return_date})"
            )
            return_rows = search_flights_tool(
                origin=destination,
                destination=origin,
                depart_date=return_date,
                return_date="",
            )
            if return_rows:
                sorted_return_rows = _enrich_rows(return_rows, return_date)
                best_return = sorted_return_rows[0]
                ret_price = (
                    f"{best_return.get('price_value'):.2f}"
                    if best_return.get("price_value") is not None else "n/d"
                )
                logger.log_event(
                    "FLIGHTS",
                    "RESULT",
                    f"Proposta ritorno: {best_return.get('title', 'N/D')} | prezzo stimato: {ret_price}"
                )
                print("\nProposta ritorno trovata:")
                print(f"- {best_return.get('title', 'N/D')}")
                print(f"- Data ritorno: {best_return.get('depart_date', 'n/d')}")
                print(f"- Orario ritorno: {best_return.get('depart_time', 'n/d')}")
                if best_return.get("url"):
                    print(f"- Link: {best_return.get('url')}")
            else:
                logger.log_event("FLIGHTS", "WARNING", "Nessuna opzione ritorno trovata.")
                print("\nNessuna opzione ritorno trovata per la data indicata.")
        choice = input(
            "Confermi questa/e opzione/i? (s=ok / n=cambia data / skip=continua senza volo): "
        ).strip().lower()

        if choice == "s":
            selected = {
                "title": best.get("title", "N/D"),
                "url": best.get("url", ""),
                "source": best.get("source", "serpapi"),
                "price_value": best.get("price_value"),
                "depart_date": best.get("depart_date", current_depart_date or "n/d"),
                "depart_time": best.get("depart_time", "n/d"),
                "origin": origin,
                "destination": destination,
                "return_date": return_date or None,
                "return_title": best_return.get("title", "n/d") if best_return else "n/d",
                "return_url": best_return.get("url", "") if best_return else "",
                "return_price_value": best_return.get("price_value") if best_return else None,
                "return_depart_date": best_return.get("depart_date", return_date or "n/d") if best_return else (return_date or "n/d"),
                "return_depart_time": best_return.get("depart_time", "n/d") if best_return else "n/d",
            }
            summary = (
                f"Best option confirmed: {selected.get('title', 'N/D')} "
                f"(date: {selected.get('depart_date', 'n/d')}, "
                f"time: {selected.get('depart_time', 'n/d')})"
            )
            if return_date:
                summary += (
                    f" | Return: {selected.get('return_title', 'n/d')} "
                    f"(date: {selected.get('return_depart_date', 'n/d')}, "
                    f"time: {selected.get('return_depart_time', 'n/d')})"
                )
            return {
                "flight_options": [selected],
                "flight_summary": summary,
                "flight_confidence_score": 0.8 if best.get("price_value") is not None else 0.5,
                "depart_date": current_depart_date or None,
            }

        if choice == "n":
            new_date = input("Nuova data andata (YYYY-MM-DD): ").strip()
            while not new_date:
                logger.log_event("FLIGHTS", "WARNING", "Data andata mancante: richiesta obbligatoria.")
                new_date = input("Inserisci la nuova data andata (YYYY-MM-DD): ").strip()
            current_depart_date = new_date
            continue

        # skip o input non riconosciuto => prosegui senza bloccare il flusso
        return {
            "flight_options": [],
            "flight_summary": "Flight suggestions collected but not confirmed by user.",
            "flight_confidence_score": 0.4,
            "depart_date": current_depart_date or None,
        }

    return {
        "flight_options": [],
        "flight_summary": "Flight search stopped after max attempts.",
        "flight_confidence_score": 0.0,
        "depart_date": current_depart_date or None,
    }

# --- 3. PLANNER NODE (RIFATTO) ---
def trip_planner_node(state: TravelAgentState):
    logger.log_event("PLANNER", "START", "Pianificazione")
    
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
    
    # Parsing JSON planner output
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

    # Tavily pricing removed: no external cost estimation in finder.

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
        logger.log_event("FINDER", "WARNING", f"Budget critico rilevato: {daily_budget}€/giorno.")

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
                validated_places.append({
                    "name": real_place.get("name"),
                    "address": real_place.get("address"),
                    "rating": real_place.get("rating", "N/A"),
                    "description": "Verificato con Google Maps"
                })
                logger.log_event("FINDER", "RESULT", f"Trovato: {real_place.get('name')}")
                day_print_lines.append(
                    f"{real_place.get('name')} | {real_place.get('address')} | rating: {real_place.get('rating', 'N/A')}"
                )
            else:
                logger.log_event("FINDER", "WARNING", f"Nessun match per: {place_name}")
                validated_places.append({
                    "name": place_name,
                    "address": place.get("address", "N/A"),
                    "rating": "N/A",
                    "description": "Non verificato (Verifica quota API)"
                })
                day_print_lines.append(
                    f"{place_name} | {place.get('address', 'N/A')} | rating: N/A"
                )
        
        day['places'] = validated_places
        updated_itinerary.append(day)

        if day_print_lines:
            print(f"\nLuoghi selezionati (giorno {day.get('day_number', '?')}):")
            for line in day_print_lines:
                print(f"- {line}")
        
    return {"budget_context": "", "itinerary": updated_itinerary}

# --- 5. CONFIDENCE NODE (POST-FINDER) ---
def confidence_evaluator_node(state: TravelAgentState):
    logger.log_event("CONFIDENCE", "START", "Valutazione confidenza post-verifica")

    itinerary = state.get("itinerary", [])
    reasons = []
    if not itinerary:
        confidence = 0.0
        reasons.append("Itinerario vuoto")
    else:
        confidence = 0.8

        unverified = 0
        total_places = 0

        for day in itinerary:
            for place in day.get("places", []):
                total_places += 1
                if place.get("description", "").startswith("Non verificato"):
                    unverified += 1

        if total_places > 0:
            unverified_ratio = unverified / total_places
            confidence -= 0.4 * unverified_ratio
            if unverified > 0:
                reasons.append(f"{unverified}/{total_places} luoghi non verificati")

        budget_total = state.get("budget_total")
        total_budget = extract_budget_number(str(budget_total)) if budget_total else extract_budget_number(state.get("budget", ""))
        num_days = int(state['days']) if state['days'].isdigit() else 1
        daily_budget = total_budget / num_days
        if daily_budget < 60:
            confidence -= 0.1
            reasons.append(f"Budget giornaliero basso ({round(daily_budget, 2)}€)")

    confidence = max(0.0, min(1.0, round(confidence, 2)))
    logger.log_event("CONFIDENCE", "INFO", f"Confidenza Agente: {confidence}")

    if confidence < 0.7:
        reason_text = "; ".join(reasons) if reasons else "Motivo non specificato"
        logger.log_event(
            "CONFIDENCE",
            "WARNING",
            f"Confidenza bassa ({confidence}). Motivi: {reason_text}. Richiesta revisione manuale."
        )
    return {"confidence_score": confidence, "critic_feedback": state.get("critic_feedback")}

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
        return {
            "is_approved": False,
            "critic_feedback": motivo,
            "retry_count": state.get("retry_count", 0) + 1
        }
    

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
