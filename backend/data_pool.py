import os
import json
from upstash_redis import Redis
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

# Configuration for Vercel KV or Upstash
KV_URL = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")

redis_client = None
if KV_URL and KV_TOKEN:
    try:
        # upstash-redis expects the URL to start with https://
        url = KV_URL
        if not url.startswith("http"):
            url = f"https://{url}"
        redis_client = Redis(url=url, token=KV_TOKEN)
    except:
        redis_client = None

POOL_DIR = os.path.join(os.path.dirname(__file__), "pool")

# Detect local or serverless environment
if not os.access(os.path.dirname(__file__), os.W_OK):
    POOL_DIR = "/tmp/form_pool"

try:
    if not redis_client:
        os.makedirs(POOL_DIR, exist_ok=True)
except:
    POOL_DIR = None

def save_to_pool(category: str, values: list):
    """Save unique values to category pool (File first, then Redis)"""
    new_vals = [v.strip() for v in values if v.strip()]
    if not new_vals: return

    # 1. Always update Local Files
    if POOL_DIR:
        file_path = os.path.join(POOL_DIR, f"{category}.json")
        try:
            existing = []
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing = json.load(f)
            
            # Case-insensitive deduplication
            existing_lower = [v.lower() for v in existing]
            to_add = [v for v in new_vals if v.lower() not in existing_lower]
            
            if to_add:
                new_pool = list(existing + to_add)
                with open(file_path, "w") as f:
                    json.dump(new_pool, f, indent=2)
        except Exception as e:
            print(f"File save error: {e}")

    # 2. Sync to Redis if available
    if redis_client:
        try:
            key = f"pool:{category}"
            # Bulk add for efficiency
            redis_client.sadd(key, *new_vals)
        except Exception as e:
            print(f"Redis sync error: {e}")

def get_from_pool(category: str):
    """Retrieve values for a category (Local File preferred)"""
    # 1. Try Local Files first
    if POOL_DIR:
        file_path = os.path.join(POOL_DIR, f"{category}.json")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return json.load(f)
        except:
            pass

    # 2. Fallback to Vercel KV (Redis)
    if redis_client:
        try:
            key = f"pool:{category}"
            members = redis_client.smembers(key)
            return list(members) if members else []
        except:
            pass

    return []

def smart_add_name(full_name: str):
    """Splits full name and adds to first_names and last_names pools with deduplication"""
    parts = full_name.strip().split()
    if not parts: return
    
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    if first:
        save_to_pool("first_names", [first])
    if last:
        save_to_pool("last_names", [last])
    
    # Also keep the full name
    save_to_pool("random_names", [full_name])
    return {"first": first, "last": last}
