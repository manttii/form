import requests
import time

BASE_URL = "http://127.0.0.1:8001" # Using port 8001 as previously established

print("--- Phase 1: Identity Authentication ---")
response = requests.post(f"{BASE_URL}/login")
token = response.json().get("access_token")
print(f"Acquired JWT for identity 'admin_user'\n")

headers = {"Authorization": f"Bearer {token}"}

print("--- Phase 2: Token Bucket Siege ---")
print("Bursting 10 requests with 0.3s delay...")
print("Capacity: 5, Refill: 0.5 tokens/sec\n")

for i in range(1, 11):
    res = requests.get(f"{BASE_URL}/secure-data", headers=headers)
    
    if res.status_code == 200:
        print(f"Request {i}: SUCCESS [200 OK]")
    elif res.status_code == 429:
        print(f"Request {i}: BLOCKED [429] -> {res.json()['detail']}")
    
    time.sleep(0.3)

print("\nWaiting 4 seconds for bucket to refill...")
time.sleep(4)

print("\nSending 2 more requests...")
for i in range(11, 13):
    res = requests.get(f"{BASE_URL}/secure-data", headers=headers)
    print(f"Request {i}: {'SUCCESS' if res.status_code == 200 else 'BLOCKED'} [{res.status_code}]")
