import os
import re
import json
import urllib.parse
import urllib.request
import urllib.error
from datetime import date, timedelta
from tavily import TavilyClient
from app.core.logger import logger
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
serpapi_key = os.getenv("SERPAPI_API_KEY")


_AIRPORT_ALIASES = {
    # Italy
    "pisa": "PSA",
    "bari": "BRI",
    "roma": "FCO",
    "rome": "FCO",
    "milano": "MXP",
    "milan": "MXP",
    "napoli": "NAP",
    "naples": "NAP",
    "torino": "TRN",
    "turin": "TRN",
    "bologna": "BLQ",
    "venezia": "VCE",
    "venice": "VCE",
    "firenze": "FLR",
    "florence": "FLR",
    "palermo": "PMO",
    "catania": "CTA",
    "cagliari": "CAG",
    "genova": "GOA",
    "genoa": "GOA",
}


def _normalize_airport_id(raw_value: str) -> str:
    """
    Converte input utente (città/aeroporto/codice) nel formato richiesto da SerpApi.
    - Se trova un codice IATA (3 lettere) lo usa.
    - Altrimenti prova alias città -> IATA.
    - In fallback usa i primi 3 caratteri uppercase.
    """
    value = (raw_value or "").strip()
    if not value:
        return ""

    upper = value.upper()
    if re.fullmatch(r"[A-Z]{3}", upper):
        return upper

    # Esempio: "Pisa (PSA)".
    m = re.search(r"\(([A-Za-z]{3})\)", value)
    if m:
        return m.group(1).upper()

    lower = value.lower()
    for key, code in _AIRPORT_ALIASES.items():
        if key in lower:
            return code

    # Fallback conservativo.
    letters = re.sub(r"[^A-Za-z]", "", value).upper()
    if len(letters) >= 3:
        return letters[:3]
    return upper[:3]

def _normalize_outbound_date(depart_date: str) -> str:
    """
    SerpApi Google Flights richiede outbound_date in formato YYYY-MM-DD.
    Se input non valido, usa una data di fallback (oggi + 30 giorni).
    """
    text = (depart_date or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text

    # Supporta input naturali tipo "1 marzo", "01 MARZO", "1 March".
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
            year = date.today().year
            try:
                parsed = date(year, month, day)
                # Se già passata, sposta all'anno prossimo.
                if parsed < date.today():
                    parsed = date(year + 1, month, day)
                return parsed.isoformat()
            except ValueError:
                pass
    return (date.today() + timedelta(days=30)).isoformat()


def _normalize_return_date(return_date: str) -> str:
    text = (return_date or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return ""


def _price_to_float(price_value):
    if isinstance(price_value, (int, float)):
        return float(price_value)
    if isinstance(price_value, str):
        match = re.search(r"([0-9]+(?:[.,][0-9]{1,2})?)", price_value)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                return None
    return None

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
    Cerca opzioni voli tramite SerpApi (Google Flights) e ritorna risultati strutturati.
    """
    try:
        if not serpapi_key:
            logger.log_event("TOOL", "ERROR", "SERPAPI_API_KEY missing.")
            return []

        origin_id = _normalize_airport_id(origin)
        destination_id = _normalize_airport_id(destination)
        outbound_date = _normalize_outbound_date(depart_date)
        inbound_date = _normalize_return_date(return_date)

        params = {
            "engine": "google_flights",
            "departure_id": origin_id,
            "arrival_id": destination_id,
            "outbound_date": outbound_date,
            "currency": "EUR",
            "hl": "it",
            "gl": "it",
            "api_key": serpapi_key,
        }
        if inbound_date:
            params["type"] = 1  # round trip
            params["return_date"] = inbound_date
        else:
            params["type"] = 2  # one way

        endpoint = f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(endpoint, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        flight_rows = []
        max_options = 6
        for block_name in ("best_flights", "other_flights"):
            for option in payload.get(block_name, []):
                if len(flight_rows) >= max_options:
                    break
                flights = option.get("flights", [])
                first_leg = flights[0] if flights else {}
                last_leg = flights[-1] if flights else {}

                dep_air = first_leg.get("departure_airport", {}) or {}
                arr_air = last_leg.get("arrival_airport", {}) or {}
                airline = first_leg.get("airline", "N/D")

                dep_code = dep_air.get("id", origin_id)
                arr_code = arr_air.get("id", destination_id)
                dep_time = dep_air.get("time", "n/d")
                arr_time = arr_air.get("time", "n/d")

                stops = max(len(flights) - 1, 0)
                duration = option.get("total_duration", "n/d")
                price_raw = option.get("price")
                price_value = _price_to_float(price_raw)
                price_text = f"{price_value:.2f}" if price_value is not None else str(price_raw or "n/d")

                title = f"{airline} {dep_code}->{arr_code}"
                content = (
                    f"Departure {dep_time} | Arrival {arr_time} | "
                    f"Stops {stops} | Duration {duration} | Price {price_text}"
                )
                url = payload.get("search_metadata", {}).get("google_flights_url", "")

                logger.log_event("SERPAPI_FLIGHTS", "RESULT", title)
                logger.log_event("SERPAPI_FLIGHTS", "INFO", content)

                flight_rows.append({
                    "title": title,
                    "content": content,
                    "raw_content": json.dumps(option, ensure_ascii=False),
                    "url": url,
                    "source": "serpapi",
                    "price_value": price_value,
                    "depart_time": dep_time,
                    "arrival_time": arr_time,
                    "stops": str(stops),
                    "duration": str(duration),
                })
            if len(flight_rows) >= max_options:
                break

        return flight_rows
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        logger.log_event("TOOL", "ERROR", f"SerpApi HTTP {e.code}: {body[:400] or str(e)}")
        return []
    except Exception as e:
        logger.log_event("TOOL", "ERROR", f"SerpApi flights error: {e}")
        return []
