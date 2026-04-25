from enum import Enum

class LocationType(Enum):
    DISTRICT = "District"
    FACILITY = "Facility"

class TimePeriod(Enum):
    MORNING_PEAK = "Morning Peak"
    AFTERNOON = "Afternoon"
    EVENING_PEAK = "Evening Peak"
    NIGHT = "Night"