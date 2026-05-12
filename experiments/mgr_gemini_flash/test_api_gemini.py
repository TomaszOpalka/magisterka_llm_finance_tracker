import asyncio
import httpx
from datetime import datetime

# Server configuration (Gemini Flash Version)
# Port is 8002 according to test_models.py
BASE_URL = "http://127.0.0.1:8002"

async def run_integration_test():
    """
    Stand-alone integration test for Finance Track API.
    Flow: Create -> Sync -> Verify
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print(f"[{datetime.now()}] Starting Integration Test at {BASE_URL}...")

        # 1. Create a test asset
        asset_data = {
            "ticker_symbol": "AAPL",
            "last_price": 0.0,
            "market_cap": 3000000000000
        }
        print("Step 1: Creating test asset 'AAPL'...")
        response = await client.post("/assets", json=asset_data)
        
        if response.status_code == 201 or response.status_code == 200:
            data = response.json()
            print(f"Success: Created asset with asset_id: {data.get('asset_id')}")
        elif response.status_code == 400 or response.status_code == 409:
            print("Note: Asset might already exist, proceeding to sync.")
        else:
            print(f"Failed to create asset: {response.text}")
            return

        # 2. Trigger Synchronization
        print("Step 2: Triggering market data synchronization...")
        sync_response = await client.post("/assets/sync")
        if sync_response.status_code == 200:
            print("Success: Price synchronization completed.")
        else:
            print(f"Sync failed: {sync_response.text}")
            return

        # 3. Verify Data Integrity
        print("Step 3: Fetching 'AAPL' to verify updates...")
        get_response = await client.get("/assets/AAPL")
        if get_response.status_code == 200:
            asset = get_response.json()
            price = asset['last_price']
            updated_at = asset['last_updated']
            
            print(f"Verification Results for asset_id {asset['asset_id']}:")
            print(f" - Ticker: {asset['ticker_symbol']}")
            print(f" - Price: {price}")
            print(f" - Last Updated: {updated_at}")

            # Assertions
            assert price > 0, "Price should be greater than 0 after sync"
            assert updated_at is not None, "last_updated should not be null"
            print("\nRESULT: Integration Test Passed Successfully!")
        else:
            print(f"Verification failed: {get_response.text}")

if __name__ == "__main__":
    try:
        asyncio.run(run_integration_test())
    except ConnectionError:
        print(f"Error: Could not connect to the server at {BASE_URL}. Is FastAPI running?")
    except Exception as e:
        print(f"Test crashed with error: {e}")
