import os
import googlemaps
from langchain_core.tools import tool
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

# Inizializziamo il client Google Maps
api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=api_key) if api_key else None

@tool
def find_places_on_maps(query: str):
    """
    Cerca luoghi reali su Google Maps tramite Places API.
    Input: Una query di ricerca (es. "Ristoranti tipici a Montmartre").
    Output: Testo con nomi, indirizzi e rating dei luoghi trovati.
    """
    if not gmaps:
        return "[ERRORE] Manca la GOOGLE_MAPS_API_KEY nel file .env!"

    logger.log_event("TOOL", "ACTION", f"🌍 Ricerca REALE su Maps per: '{query}'")
    
    try:
        # Usiamo l'API 'places' per cercare luoghi testuali
        results = gmaps.places(query=query)
        
        if not results or 'results' not in results:
            return f"Nessun risultato trovato per '{query}'."

        # Prendiamo i primi 3 risultati per non sovraccaricare l'LLM
        top_results = results['results'][:3]
        formatted_output = ""

        for place in top_results:
            name = place.get('name', 'Sconosciuto')
            address = place.get('formatted_address', 'Indirizzo non disponibile')
            rating = place.get('rating', 'N/A')
            user_ratings_total = place.get('user_ratings_total', 0)
            
            formatted_output += (
                f"NOME: {name}\n"
                f"INDIRIZZO: {address}\n"
                f"RATING: {rating}/5 ({user_ratings_total} recensioni)\n"
                f"---\n"
            )
            
        return formatted_output

    except Exception as e:
        error_msg = f"Errore durante la chiamata a Google Maps: {str(e)}"
        logger.log_event("TOOL", "ERROR", error_msg)
        return error_msg