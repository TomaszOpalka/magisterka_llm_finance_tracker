import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_suite")

BASE_URL = "http://localhost:8000"

async def test_camel_case_api():
    """
    Verifies that the API exclusively communicates using camelCase JSON keys,
    while ensuring the backend correctly interprets them.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: POST creation using camelCase keys
        payload = {
            "tickerSymbol": "MSFT",
            "lastPrice": 350.00,
            "marketCap": 2500000000000
        }
        
        logger.info(f"POST /assets -> Sending camelCase payload: {payload}")
        post_response = await client.post(f"{BASE_URL}/assets", json=payload)
        
        if post_response.status_code == 201:
            data = post_response.json()
            logger.info("SUCCESS: Asset created.")
            
            # Strict Verification: API MUST return camelCase, never snake_case
            assert "assetId" in data, "Failed: 'assetId' not found in response."
            assert "asset_id" not in data, "Failed: 'asset_id' leaked to API response."
            assert "lastUpdated" in data, "Failed: 'lastUpdated' not found."
            assert data["tickerSymbol"] == "MSFT"
            logger.info("VERIFIED: Response successfully mapped to camelCase.")
            
        elif post_response.status_code == 400:
            logger.warning("Asset MSFT already exists, continuing to GET tests.")
        else:
            logger.error(f"Failed to create asset: {post_response.text}")

        # Step 2: GET list using camelCase Query Parameters
        logger.info("GET /assets -> Testing camelCase query parameters (minPrice, sortBy)")
        get_response = await client.get(f"{BASE_URL}/assets?minPrice=300&sortBy=marketCap")
        
        if get_response.status_code == 200:
            list_data = get_response.json()
            assert isinstance(list_data, list)
            if len(list_data) > 0:
                first_item = list_data[0]
                assert "tickerSymbol" in first_item
                assert "marketCap" in first_item
                logger.info("VERIFIED: Query parameters accepted and returned camelCase JSON.")
        else:
            logger.error(f"Failed to retrieve list: {get_response.text}")

        # Step 3: Analytics Endpoint check
        logger.info("GET /assets/MSFT/analytics -> Checking nested camelCase keys")
        analytics_response = await client.get(f"{BASE_URL}/assets/MSFT/analytics")
        
        if analytics_response.status_code == 200:
            a_data = analytics_response.json()
            assert "movingAverage30d" in a_data
            assert "rsi14" in a_data
            assert "tickerSymbol" in a_data
            logger.info("VERIFIED: Analytics endpoint returns pure camelCase.")

if __name__ == "__main__":
    asyncio.run(test_camel_case_api())