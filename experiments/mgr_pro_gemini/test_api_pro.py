import asyncio
import httpx
import logging
import sys

# Configure basic logging for the test script (Gemini PRO Version)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("test_api")

# Gemini PRO port is 8001 according to test_models.py
BASE_URL = "http://127.0.0.1:8001"

async def run_automated_tests():
    """
    Asynchronous test suite utilizing httpx to verify the core functionality
    of the Finance Track API, ensuring error resilience and data updates.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        
        # Step 1: Create a test asset
        logger.info(f"--- STEP 1: Creating test asset (AAPL) at {BASE_URL} ---")
        payload = {
            "ticker_symbol": "AAPL",
            "last_price": 0.0, # Initializing with 0.0 to test the update mechanism
            "market_cap": 3000000000000
        }
        
        post_response = await client.post("/assets", json=payload)
        
        if post_response.status_code == 201:
            logger.info("Asset successfully created.")
        elif post_response.status_code == 400 or post_response.status_code == 409:
            logger.info("Asset already exists. Proceeding with tests...")
        else:
            logger.error(f"Failed to create asset. Status: {post_response.status_code}, Response: {post_response.text}")
            return

        # Step 2: Trigger synchronization
        logger.info("--- STEP 2: Triggering price synchronization ---")
        sync_response = await client.post("/assets/sync")
        
        assert sync_response.status_code == 200, f"Sync endpoint failed: {sync_response.text}"
        logger.info("Sync triggered successfully.")

        # Step 3: Fetch asset and assert data integrity
        logger.info("--- STEP 3: Fetching asset and validating updates ---")
        get_response = await client.get("/assets/AAPL")
        
        assert get_response.status_code == 200, "Failed to fetch asset from database."
        asset_data = get_response.json()
        
        logger.info(f"Retrieved Asset Data: {asset_data}")
        
        # Assertions
        assert "asset_id" in asset_data, "CRITICAL: 'asset_id' must be present in the response."
        assert "id" not in asset_data, "CRITICAL: 'id' should not be used as primary key identifier (违反 PR #67)."
        assert asset_data["last_price"] > 0.0, "Test Failed: last_price was not updated (still 0.0)."
        assert asset_data["last_updated"] is not None, "Test Failed: last_updated timestamp is null."
        
        logger.info("--- ALL TESTS PASSED SUCCESSFULLY ---")

if __name__ == "__main__":
    asyncio.run(run_automated_tests())
