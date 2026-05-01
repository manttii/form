import os
import json

POOL_DIR = os.path.join(os.path.dirname(__file__), "pool")
os.makedirs(POOL_DIR, exist_ok=True)

def save_to_pool(category: str, values: list):
    """Save unique values to a category file (names, emails, etc.)"""
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    
    existing = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                existing = json.load(f)
        except:
            existing = []
            
    # Add unique new values
    new_pool = list(set(existing + [v.strip() for v in values if v.strip()]))
    
    with open(file_path, "w") as f:
        json.dump(new_pool, f)

def get_from_pool(category: str):
    """Retrieve values for a category"""
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []
