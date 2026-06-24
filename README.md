# Token Bucket Rate Limiter

Despite the repository name, this project is a backend security implementation demonstrating an advanced Rate Limiting system.

## 🏗️ Architecture & Features

- **Framework**: Built with **FastAPI** (Python).
- **Token Bucket Algorithm**: Implements a highly efficient rate-limiting algorithm, decentralized via **Redis**.
- **JWT Authentication**: Identifies users and enforces per-user API rate limits securely.
- **Automatic Replenishment**: Continuously refills the token bucket (e.g., 1 token every 2 seconds).
- **Graceful Degradation**: Includes an automatic fallback to `fakeredis` for local simulation when an actual Redis server isn't available.

## 🚀 Getting Started

1. Ensure you have Python 3.8+ installed.
2. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn redis fakeredis pyjwt
   ```
3. Run the FastAPI server:
   ```bash
   uvicorn server:app --reload
   ```
4. Access the API documentation at `http://127.0.0.1:8000/docs`.
