from typing import TypedDict, List, Optional

class PlaceInfo(TypedDict):
    name: str
    address: str
    rating: str
    description: str

class DayPlan(TypedDict):
    day_number: int
    focus: str
    places: List[PlaceInfo]

class TravelAgentState(TypedDict):
    destination: str
    days: int
    interests: str
    travel_style: str
    draft_schedule: List[str]
    itinerary: List[DayPlan]
    feedback: Optional[str]
    is_approved: bool
    retry_count: int