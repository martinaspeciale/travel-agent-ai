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
    
    # Output
    travel_style: str
    itinerary: List[DayPlan]  
    
    # Controllo
    critic_feedback: Optional[str]
    budget_context: Optional[str]
    confidence_score: float
    is_approved: bool
    retry_count: int
