import pytest
from experiments.mgr_gemini_flash.analytics import calculate_moving_average, calculate_rsi

@pytest.mark.asyncio
async def test_calculate_moving_average():
    """Test the Simple Moving Average logic."""
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = calculate_moving_average(prices)
    assert result == 30.0
    
    empty_result = calculate_moving_average([])
    assert empty_result is None

@pytest.mark.asyncio
async def test_calculate_rsi():
    """Test the RSI calculation logic with a standard period."""
    # RSI expects at least period + 1 data points
    prices = [100.0, 110.0, 105.0, 115.0, 120.0, 110.0, 100.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
    result = calculate_rsi(prices, periods=14)
    assert result is not None
    assert 0 <= result <= 100
    
    # Test insufficient data
    short_prices = [100.0, 110.0]
    assert calculate_rsi(short_prices, periods=14) is None

@pytest.mark.asyncio
async def test_create_and_get_asset(client):
    """Integration test for POST /assets and GET /assets/{ticker_symbol}."""
    # 1. Test POST /assets
    asset_payload = {
        "ticker_symbol": "MSFT",
        "last_price": 420.50,
        "market_cap": 3000000000000
    }
    post_response = await client.post("/assets", json=asset_payload)
    assert post_response.status_code == 201
    data = post_response.json()
    assert data["ticker_symbol"] == "MSFT"
    assert "asset_id" in data  # Ensure custom asset_id is generated
    assert isinstance(data["asset_id"], str)

    # 2. Test GET /assets/{ticker_symbol}
    get_response = await client.get("/assets/MSFT")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["ticker_symbol"] == "MSFT"
    assert get_data["asset_id"] == data["asset_id"]

@pytest.mark.asyncio
async def test_get_non_existent_asset(client):
    """Test retrieving an asset that does not exist."""
    response = await client.get("/assets/NONEXISTENT")
    assert response.status_code == 404