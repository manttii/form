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
    """Save unique values to category pool (Redis or File)"""
    new_vals = [v.strip() for v in values if v.strip()]
    if not new_vals: return

    # 1. Try Vercel KV (Redis) first
    if redis_client:
        try:
            key = f"pool:{category}"
            # SADD adds unique elements to a set
            for v in new_vals:
                redis_client.sadd(key, v)
            return
        except Exception as e:
            print(f"Redis save error: {e}")

    # 2. Fallback to Local Files
    if not POOL_DIR: return
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    try:
        existing = []
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                existing = json.load(f)
        
        new_pool = list(set(existing + new_vals))
        with open(file_path, "w") as f:
            json.dump(new_pool, f)
    except:
        pass

def get_from_pool(category: str):
    """Retrieve values for a category (Redis or File)"""
    # 1. Try Vercel KV (Redis)
    if redis_client:
        try:
            key = f"pool:{category}"
            # SMEMBERS gets all elements from a set
            members = redis_client.smembers(key)
            return list(members) if members else []
        except:
            pass

    # 2. Fallback to Local Files
    if not POOL_DIR: return []
    file_path = os.path.join(POOL_DIR, f"{category}.json")
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []
