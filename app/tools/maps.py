import os
import googlemaps
from langchain_core.tools import tool
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=api_key) if api_key else None

@tool
def find_places_on_maps(query: str):
    """
    Cerca luoghi reali su Google Maps. 
    Ritorna una lista di risultati strutturati per il Finder.
    """
    if not gmaps:
        return []

    try:
        # Esegue la ricerca
        response = gmaps.places(query=query)
        
        # Gestione errori di quota o permessi (se abbiamo esaurito le chiamate)
        if response.get('status') != 'OK':
            logger.log_event("TOOL", "ERROR", f"Maps Status: {response.get('status')}")
            return []

        results = response.get('results', [])
        if not results:
            return []

        # Estraiamo solo i dati necessari in formato lista di dict
        structured_data = []
        for place in results[:1]:  # Prendiamo il top result
            structured_data.append({
                "name": place.get('name'),
                "address": place.get('formatted_address'),
                "rating": place.get('rating', 'N/A'),
                "place_id": place.get('place_id')
            })
        
        return structured_data

    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"Eccezione Maps: {str(e)}")
        return []