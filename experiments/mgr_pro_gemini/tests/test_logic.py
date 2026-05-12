import pytest
from httpx import AsyncClient
from experiments.mgr_pro_gemini import analytics

# --- Unit Tests for Analytics (analytics.py) ---

@pytest.mark.asyncio
async def test_calculate_moving_average():
    """Validates the 30-day SMA logic, including mathematical accuracy and edge cases."""
    # Setup 30 days of price data
    prices = [10.0] * 29
    prices.append(40.0) # Last day spikes to 40.0
    
    # Expected SMA = ((29 * 10.0) + 40.0) / 30 = 330.0 / 30 = 11.0
    sma = analytics.calculate_moving_average(prices, period=30)
    assert sma == 11.0000

    # Edge Case: Insufficient data (e.g., only 29 days)
    short_prices = [10.0] * 29
    assert analytics.calculate_moving_average(short_prices, period=30) is None


@pytest.mark.asyncio
async def test_calculate_rsi():
    """Validates the 14-period RSI logic, handling normal behavior, missing data, and extremes."""
    # Setup mixed price data (at least 15 points needed for 14-period RSI differences)
    prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0, 111.0, 110.0, 112.0, 114.0, 113.0, 115.0]
    
    rsi = analytics.calculate_rsi(prices, periods=14)
    assert rsi is not None
    assert 0.0 <= rsi <= 100.0

    # Edge Case: Insufficient data
    assert analytics.calculate_rsi([100.0, 101.0], periods=14) is None

    # Edge Case: Asset only goes up (0 losses) -> RSI must be exactly 100.0
    gains_only = [float(i) for i in range(100, 120)]
    rsi_max = analytics.calculate_rsi(gains_only, periods=14)
    assert rsi_max == 100.0


# --- Integration Tests for API Endpoints (main.py) ---

@pytest.mark.asyncio
async def test_create_and_get_asset(test_client: AsyncClient):
    """
    Tests the full lifecycle of creating an asset and retrieving it.
    Strictly verifies the primary key constraint (asset_id).
    """
    payload = {
        "ticker_symbol": "TSLA",
        "last_price": 250.50,
        "market_cap": 800000000000
    }

    # Step 1: Create the asset via POST
    post_response = await test_client.post("/assets", json=payload)
    assert post_response.status_code == 201, f"POST failed: {post_response.text}"
    
    post_data = post_response.json()
    
    # CRITICAL: Verify schema structure and naming conventions
    assert "asset_id" in post_data, "Primary key 'asset_id' is missing from response."
    assert "id" not in post_data, "System violation: 'id' field detected."
    assert post_data["ticker_symbol"] == "TSLA"
    assert post_data["last_price"] == 250.50
    
    asset_id = post_data["asset_id"]

    # Step 2: Retrieve the newly created asset via GET
    get_response = await test_client.get("/assets/TSLA")
    assert get_response.status_code == 200, f"GET failed: {get_response.text}"
    
    get_data = get_response.json()
    
    # Verify the retrieved data matches the created database entry
    assert get_data["asset_id"] == asset_id
    assert get_data["ticker_symbol"] == "TSLA"
    assert get_data["last_price"] == 250.50