"""
Asynchronous test script for Finance Track API (ChatGPT Version).
Run with: python test_api.py (requires the FastAPI server to be running).
"""

import asyncio
import httpx

# GPT-4o port is 8003 according to test_models.py
BASE_URL = "http://127.0.0.1:8003"


async def test_flow():
    async with httpx.AsyncClient() as client:
        print(f"Starting test flow at {BASE_URL}...")
        
        # Step 1: Create test asset
        print("Step 1: Creating test asset...")
        response = await client.post(
            f"{BASE_URL}/assets",
            json={
                "ticker_symbol": "AAPL",
                "last_price": 0,
                "market_cap": 1_000_000_000,
                "last_updated": None,
            },
        )

        # Allow 409 Conflict if asset already exists from previous runs
        if response.status_code == 409:
            print("Asset already exists, proceeding to next step.")
        else:
            assert response.status_code in (200, 201), f"Unexpected status code: {response.status_code}"
            print("Asset created successfully.")

        # Step 2: Trigger sync
        print("Step 2: Triggering price sync...")
        response = await client.post(f"{BASE_URL}/assets/sync")
        assert response.status_code == 200, f"Sync failed: {response.status_code}"

        # Step 3: Fetch asset
        print("Step 3: Fetching asset details...")
        response = await client.get(f"{BASE_URL}/assets/AAPL")
        assert response.status_code == 200, f"Fetch failed: {response.status_code}"

        data = response.json()

        # Assertions
        print(f"Verifying data: {data}")
        assert data["last_price"] != 0, "Price was not updated!"
        assert data["last_updated"] is not None, "Timestamp was not set!"

        print("TEST PASSED: Asset updated successfully")


if __name__ == "__main__":
    asyncio.run(test_flow())
