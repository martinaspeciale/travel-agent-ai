import os
from tavily import TavilyClient
from app.core.logger import logger
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

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

        search_query = f"flights from {origin} to {destination}{date_part}"

        # Domini iniziali: estendibili in seguito senza toccare il flow.
        include_domains = [
            "skyscanner.com",
            "google.com",
            "kayak.com",
            "momondo.com",
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
