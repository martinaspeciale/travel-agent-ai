import time
import random
from langchain_core.tools import tool
from logger import logger

@tool
def find_places_on_maps(query: str):
    """
    SIMULATORE DI GOOGLE MAPS (MOCK).
    Restituisce luoghi verosimili senza usare API Key a pagamento.
    """
    logger.log_event("TOOL", "ACTION", f"🔍 (MOCK) Ricerca simulata per: '{query}'")
    time.sleep(1) # Simuliamo latenza

    # Generiamo risultati basati sulle parole chiave
    query_lower = query.lower()
    city = "Città"
    if "parigi" in query_lower: city = "Parigi"
    elif "roma" in query_lower: city = "Roma"

    fake_results = []
    # Logica semplice per variare i risultati
    types = ["Bistrot", "Museo", "Parco", "Galleria"]
    for t in types:
        fake_results.append(
            f"NOME: {t} {city} Storico\n"
            f"INDIRIZZO: Via Principale, {random.randint(1, 100)}\n"
            f"RATING: {random.uniform(4.0, 5.0):.1f}/5\n"
            f"DESCRIZIONE: Un luogo perfetto per {query}.\n---\n"
        )

    return "".join(fake_results)