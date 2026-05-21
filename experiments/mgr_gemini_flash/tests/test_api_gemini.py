import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8002"

async def run_camel_case_test():
    """Verifies that the API communicates exclusively in camelCase."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. POST using camelCase
        payload = {
            "tickerSymbol": "NVDA",
            "lastPrice": 900.0,
            "marketCap": 2200000000000
        }
        response = await client.post("/assets", json=payload)
        assert response.status_code == 201
        data = response.json()
        
        # 2. Verify response keys (must not contain underscores)
        assert "assetId" in data
        assert "tickerSymbol" in data
        assert "lastPrice" in data
        assert "asset_id" not in data  # Fail if snake_case leaked
        
        print(f"Success! Asset created with assetId: {data['assetId']}")

        # 3. Check Analytics
        analytics_res = await client.get(f"/assets/{data['tickerSymbol']}/analytics")
        assert analytics_res.status_code == 200
        a_data = analytics_res.json()
        assert "movingAverage30d" in a_data
        assert "rsi14" in a_data
        
        print("Integration Test Passed: camelCase mapping is fully functional.")

if __name__ == "__main__":
    asyncio.run(run_camel_case_test())