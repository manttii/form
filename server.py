from fastapi import FastAPI, Depends, HTTPException, Request
import jwt
import time
import redis
import json

app = FastAPI()

# Redis connection with fallback to fakeredis for local simulation
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to real Redis")
except Exception:
    import fakeredis
    r = fakeredis.FakeRedis(decode_responses=True)
    print("Using fakeredis for simulation")

SECRET_KEY = "graphic_era_master_key"

# Token Bucket Configuration
BUCKET_CAPACITY = 5
REFILL_RATE = 0.5  # tokens per second (1 token every 2 seconds)

def verify_token(request: Request):
    """Extends identity extraction from JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authentication Token")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")

def check_rate_limit(user_data: dict = Depends(verify_token)):
    """The Token Bucket Shield: Identity-based and centralized via Redis."""
    user_id = user_data.get("sub")
    key = f"rate_limit:{user_id}"
    
    now = time.time()
    
    # Atomic-ish fetch of bucket state
    state_json = r.get(key)
    if state_json:
        state = json.loads(state_json)
        tokens = state['tokens']
        last_update = state['last_update']
    else:
        tokens = BUCKET_CAPACITY
        last_update = now

    # Refill tokens based on elapsed time
    elapsed = now - last_update
    tokens = min(BUCKET_CAPACITY, tokens + (elapsed * REFILL_RATE))
    
    if tokens >= 1:
        # Consume 1 token
        tokens -= 1
        r.set(key, json.dumps({'tokens': tokens, 'last_update': now}))
    else:
        # Save current tokens (refilled but not consumed) to keep progress
        r.set(key, json.dumps({'tokens': tokens, 'last_update': now}))
        raise HTTPException(
            status_code=429, 
            detail=f"HTTP 429: Token Bucket Empty for user '{user_id}'. Refilling..."
        )

@app.post("/login")
def login():
    """Identifies the user as 'admin_user'."""
    payload = {"sub": "admin_user", "exp": time.time() + 3600}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"access_token": token}

@app.get("/secure-data", dependencies=[Depends(check_rate_limit)])
def get_data():
    return {
        "message": "Access Granted.",
        "logic": "Token Bucket consumed 1 token via Redis identity check."
    }
