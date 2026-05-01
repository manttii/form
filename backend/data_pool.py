import os
import json

POOL_DIR = os.path.join(os.path.dirname(__file__), "pool")

# Detect Vercel or read-only environment
if not os.access(os.path.dirname(__file__), os.W_OK):
    # Try /tmp as fallback
    POOL_DIR = "/tmp/form_pool"

try:
    os.makedirs(POOL_DIR, exist_ok=True)
except:
    # If still not writable, just disable pooling silently
    POOL_DIR = None

def save_to_pool(category: str, values: list):
    if not POOL_DIR: return
    """Save unique values to a category file (names, emails, etc.)"""
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    
    existing = []
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing = json.load(f)
                
        # Add unique new values
        new_pool = list(set(existing + [v.strip() for v in values if v.strip()]))
        
        with open(file_path, "w") as f:
            json.dump(new_pool, f)
    except:
        pass # Fail silently in serverless

def get_from_pool(category: str):
    if not POOL_DIR: return []
    """Retrieve values for a category"""
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []
