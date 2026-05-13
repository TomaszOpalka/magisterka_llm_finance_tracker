"""
Async API tests for Finance Track.
"""

import asyncio
import httpx


BASE_URL = "http://127.0.0.1:8003"


async def test_flow():
    """
    Full API integration test.
    """

    async with httpx.AsyncClient(base_url=BASE_URL) as client:

        # Create asset
        response = await client.post(
            "/assets",
            json={
                "tickerSymbol": "AAPL",
                "lastPrice": 150.0,
                "marketCap": 3000000000000,
                "lastUpdated": None,
            },
        )

        assert response.status_code == 201
        data = response.json()

        asset_id = data["assetId"]

        # Fetch asset
        get_response = await client.get(
            "/assets/AAPL",
        )

        assert get_response.status_code == 200

        result = get_response.json()

        assert "assetId" in result
        assert result["tickerSymbol"] == "AAPL"


if __name__ == "__main__":
    asyncio.run(test_flow())