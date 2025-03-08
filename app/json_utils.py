import json
from typing import Any, Optional

def serialize_json(data: Any) -> Optional[str]:
    """Serialize data to JSON string if not already a string."""
    if data is None:
        return None
    if isinstance(data, str):
        return data
    return json.dumps(data)

def deserialize_json(data: Optional[str]) -> Any:
    """Deserialize JSON string to Python object if it's a valid JSON string."""
    if data is None:
        return None
    if not isinstance(data, str):
        return data
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return data 