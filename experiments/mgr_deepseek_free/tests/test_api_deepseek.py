"""
Integration test script for the Finance Track API (DeepSeek Version).
Uses httpx to verify asset creation, price sync, and data retrieval.
Run with: python test_api.py (requires the FastAPI server to be running).
"""

import asyncio
import httpx

# Note: In the unified validator, this port will be dynamic.
# For this specific copy, we use the default or current DeepSeek port (8004).
BASE_URL = "http://127.0.0.1:8004"


async def run_tests():
    """Main test flow: create asset, sync prices, verify updated data."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Create a test asset (AAPL) with dummy price 0
        print(f"Creating test asset (AAPL) at {BASE_URL}...")
        create_data = {
            "ticker_symbol": "AAPL",
            "last_price": 0.0,
            "market_cap": 2_500_000_000,
        }
        create_resp = await client.post("/assets", json=create_data)
        if create_resp.status_code == 409 or create_resp.status_code == 400:
            print("Asset already exists or creation failed – continuing with existing record.")
            # If it already exists, we can still proceed with sync
        else:
            assert create_resp.status_code == 201, f"Creation failed: {create_resp.text}"
            created = create_resp.json()
            print(f"Created asset with asset_id={created['asset_id']}")
            assert created["asset_id"] is not None, "asset_id must be present"
            assert created["ticker_symbol"] == "AAPL"

        # 2. Trigger price synchronization
        print("Synchronizing prices...")
        sync_resp = await client.post("/assets/sync")
        assert sync_resp.status_code == 200, f"Sync failed: {sync_resp.text}"
        sync_result = sync_resp.json()
        print(f"Sync result: {sync_result}")

        # 3. Fetch the asset and verify the price was updated
        print("Fetching AAPL asset...")
        get_resp = await client.get("/assets/AAPL")
        assert get_resp.status_code == 200, f"GET failed: {get_resp.text}"
        asset = get_resp.json()
        print(f"Fetched asset: {asset}")
        assert asset["last_price"] != 0.0, "last_price should have been updated"
        assert asset["last_updated"] is not None, "last_updated should be set"
        print("All tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
