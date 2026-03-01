import httpx
import asyncio
import time

async def test_endpoints():
    print("--- Testing Sidecar Endpoints ---")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test Root
        try:
            r = await client.get("/")
            print(f"GET /: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"GET / failed: {e}")

        # Test Metrics
        try:
            r = await client.get("/metrics")
            print(f"GET /metrics: {r.status_code}")
            # print(r.text)
        except Exception as e:
            print(f"GET /metrics failed: {e}")

        # Test Analyze
        print("Testing /analyze (this might take a few seconds if LLM is active)...")
        try:
            r = await client.get("/analyze")
            print(f"GET /analyze: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"GET /analyze failed: {e}")

        # Test Poke
        print("Testing /poke (POST)...")
        try:
            r = await client.post("/poke")
            print(f"POST /poke: {r.status_code} - {r.json()}")
        except Exception as e:
            print(f"POST /poke failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
