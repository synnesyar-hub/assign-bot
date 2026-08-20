# utils/mapping.py

from config import STATUS_MAP

def lower_status(status: str) -> str:
    if not status:
        return "unknown"
    
    return STATUS_MAP.get(status.upper(), status.lower())