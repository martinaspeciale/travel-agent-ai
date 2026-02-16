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
    Search real places on Google Maps.
    Return a structured list of results for the Finder node.
    """
    logger.log_tool("GOOGLE_MAPS", f"Verifica posizione e rating per: {query}")
    if not gmaps:
        return "Google Maps non configurato: manca GOOGLE_MAPS_API_KEY."

    try:
        # Run the search.
        response = gmaps.places(query=query)
        
        # Handle quota/permission errors (for example when quota is exhausted).
        if response.get('status') != 'OK':
            logger.log_event("TOOL", "ERROR", f"Maps Status: {response.get('status')}")
            return f"Google Maps errore: status {response.get('status')}."

        results = response.get('results', [])
        if not results:
            return []

        # Keep only required fields in a list of dicts.
        structured_data = []
        for place in results[:1]:  # Keep the top result only.
            structured_data.append({
                "name": place.get('name'),
                "address": place.get('formatted_address'),
                "rating": place.get('rating', 'N/A'),
                "place_id": place.get('place_id')
            })
        
        return structured_data

    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"Eccezione Maps: {str(e)}")
        return f"Google Maps eccezione: {str(e)}"
