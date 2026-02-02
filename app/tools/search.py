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
        
        context = ""
        for res in results['results']:
            context += f"\n- {res['content']}"
        return context
    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"Tavily error: {e}")
        return "Informazioni sui prezzi non disponibili."