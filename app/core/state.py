from typing import TypedDict, List, Optional

# Struttura di un Luogo
class PlaceInfo(TypedDict, total=False):
    name: str
    address: str
    rating: str
    description: Optional[str]

# Struttura di un Giorno
class DayPlan(TypedDict):
    day_number: int
    focus: str
    places: List[PlaceInfo]

# Opzione volo suggerita
class FlightOption(TypedDict, total=False):
    origin: str
    destination: str
    depart_date: str
    return_date: Optional[str]
    airline: str
    price: str
    duration: str
    stops: str
    source: str
    link: str

# Stato dell'Agente
class TravelAgentState(TypedDict):
    # Input
    user_input: str
    destination: str
    days: str
    interests: str
    budget: str
    budget_total: Optional[str]
    companion: str
    banned_places: Optional[List[str]]
    origin: Optional[str]
    depart_date: Optional[str]
    return_date: Optional[str]
    
    # Output
    travel_style: str
    itinerary: List[DayPlan]
    flight_options: Optional[List[FlightOption]]
    flight_summary: Optional[str]
    
    # Controllo
    critic_feedback: Optional[str]
    budget_context: Optional[str]
    confidence_score: float
    flight_confidence_score: Optional[float]
    is_approved: bool
    retry_count: int
