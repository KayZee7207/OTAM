import json
import os
import pathlib
from typing import Dict, Any

STATE_FILE = "analyzed.json"

def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_analysis(filename: str) -> Dict[str, Any]:
    state = load_state()
    # Normalize filename to be key-friendly (basename)
    key = pathlib.Path(filename).name
    return state.get(key)

def save_analysis(filename: str, data: Dict[str, Any]):
    state = load_state()
    key = pathlib.Path(filename).name
    
    # Store relevant data
    state[key] = {
        "timestamp": data.get("timestamp"), 
        "toxicity_score": data.get("toxicity_score"),
        "summary": data.get("summary"),
        "toxic_players": data.get("toxic_players", [])
    }
    save_state(state)
