# Trip, Intent, POI, Day — minimal starter
class POI(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    city: str
    neighborhood: str | None = None
    tags: list[str] = []
    duration_min: int | None = None
    popularity: float | None = None
    booking_required: bool = False
    booking_url: str | None = None
    hours: dict | None = None  # {"mon":[["09:00","17:00"]], ..., "tz":"America/New_York"}
    notes: list[str] = []
    source: str
    source_id: str
