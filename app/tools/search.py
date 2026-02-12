import os
import re
from tavily import TavilyClient
from app.core.logger import logger
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def _is_flight_result(title: str, content: str, url: str, origin: str, destination: str) -> bool:
    text = f"{title} {content} {url}".lower()
    origin_l = (origin or "").strip().lower()
    destination_l = (destination or "").strip().lower()

    positive_markers = [
        "flight", "flights", "airfare", "airline", "volo", "voli",
        "andata", "ritorno", "departure", "arrival", "round trip", "one way",
    ]
    negative_markers = [
        "car rental", "car-rental", "noleggio auto",
        "hotel", "booking hotel", "vacation rental", "taxi", "bus", "train",
        "parking", "cruise", "traghetto", "ferry", "hostel",
    ]

    if any(marker in text for marker in negative_markers):
        return False

    if not any(marker in text for marker in positive_markers):
        return False

    # Richiediamo anche un minimo di segnale sulla tratta richiesta.
    route_signals = 0
    if origin_l and origin_l in text:
        route_signals += 1
    if destination_l and destination_l in text:
        route_signals += 1
    return route_signals >= 1

def search_prices_tool(query: str):
    """
    Cerca su internet i prezzi attuali e consigli per risparmiare.
    """
    try:
        # Cerchiamo informazioni specifiche sui costi
        search_query = f"ticket prices and free things to do {query}"
        results = tavily_client.search(query=search_query, max_results=2)
        
        context_lines = []
        for res in results.get('results', []):
            title = res.get('title', 'Senza titolo')
            content = res.get('content', '').strip()

            # Log in output: cosa ha trovato e dove
            logger.log_event("TAVILY", "RESULT", f"{title}")
            if content:
                logger.log_event("TAVILY", "INFO", content[:240])

            # Contesto per il critic (senza URL)
            context_lines.append(f"- {title}: {content}")

        if not context_lines:
            return "Nessun risultato Tavily disponibile."

        return "\n".join(context_lines)
    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"Tavily error: {e}")
        return "Informazioni sui prezzi non disponibili."


def search_flights_tool(origin: str, destination: str, depart_date: str = "", return_date: str = ""):
    """
    Cerca opzioni voli tramite Tavily, limitando le fonti a domini travel affidabili.
    Ritorna una lista di risultati grezzi (title/content/url) da far elaborare ai nodi.
    """
    try:
        date_part = f" depart {depart_date}" if depart_date else ""
        if return_date:
            date_part += f" return {return_date}"

        search_query = (
            f"best flights from {origin} to {destination}{date_part} "
            "airfare economy round trip one way"
        )

        # Domini iniziali: estendibili in seguito senza toccare il flow.
        include_domains = [
            "skyscanner.com",
            "kayak.com",
            "momondo.com",
            "expedia.com",
        ]

        results = tavily_client.search(
            query=search_query,
            max_results=5,
            include_domains=include_domains,
        )

        flight_rows = []
        for res in results.get("results", []):
            title = res.get("title", "No title")
            content = (res.get("content") or "").strip()
            url = res.get("url", "")

            logger.log_event("TAVILY_FLIGHTS", "RESULT", title)
            if content:
                logger.log_event("TAVILY_FLIGHTS", "INFO", content[:240])

            if not _is_flight_result(title, content, url, origin, destination):
                logger.log_event("TAVILY_FLIGHTS", "SKIP", f"Non-flight result filtered: {title}")
                continue

            flight_rows.append({
                "title": title,
                "content": content,
                "url": url,
                "source": "tavily",
            })

        return flight_rows
    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"Tavily flights error: {e}")
        return []
