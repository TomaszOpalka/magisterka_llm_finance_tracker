"""
Integration test script for the Finance Track API.
Uses httpx to verify asset creation, price sync, and data retrieval,
now with camelCase JSON keys.
Run with: python test_api.py (requires the FastAPI server to be running).
"""

import asyncio

import httpx

BASE_URL = "http://127.0.0.1:8000"


async def run_tests():
    """Main test flow: create asset, sync prices, verify updated data."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Create a test asset (AAPL) with dummy price 0
        print("Creating test asset (AAPL)…")
        create_data = {
            "tickerSymbol": "AAPL",
            "lastPrice": 0.0,
            "marketCap": 2_500_000_000,
        }
        create_resp = await client.post("/assets", json=create_data)
        if create_resp.status_code == 409:
            print("Asset already exists – continuing with existing record.")
        else:
            assert create_resp.status_code == 201, f"Creation failed: {create_resp.text}"
            created = create_resp.json()
            print(f"Created asset with assetId={created['assetId']}")
            assert "assetId" in created
            assert created["tickerSymbol"] == "AAPL"

        # 2. Trigger price synchronization
        print("Synchronizing prices…")
        sync_resp = await client.post("/assets/sync")
        assert sync_resp.status_code == 200, f"Sync failed: {sync_resp.text}"
        sync_result = sync_resp.json()
        print(f"Sync result: {sync_result}")

        # 3. Fetch the asset and verify the price was updated
        print("Fetching AAPL asset…")
        get_resp = await client.get("/assets/AAPL")
        assert get_resp.status_code == 200, f"GET failed: {get_resp.text}"
        asset = get_resp.json()
        print(f"Fetched asset: {asset}")
        assert asset["lastPrice"] != 0.0, "lastPrice should have been updated"
        assert asset["lastUpdated"] is not None, "lastUpdated should be set"
        print("All tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())