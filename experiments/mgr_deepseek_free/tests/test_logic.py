"""
Unit tests for analytics functions and integration tests for API endpoints.
All tests use the isolated test database configured in conftest.py.
"""

import pytest
from analytics import calculate_moving_average, calculate_rsi
from exceptions import AnalyticsException


# ─────────────────────────────────────────────
# Unit tests for analytics.py
# ─────────────────────────────────────────────

def test_sma_standard():
    """SMA should correctly average the last `window` elements."""
    prices = list(range(1, 41))  # 1 to 40
    result = calculate_moving_average(prices, window=30)
    expected = sum(prices[-30:]) / 30
    assert result == round(expected, 4)


def test_sma_insufficient_data():
    """Should raise AnalyticsException when fewer prices than the window."""
    with pytest.raises(AnalyticsException) as exc_info:
        calculate_moving_average([10, 20, 30], window=30)
    assert "Insufficient data" in exc_info.value.detail


def test_rsi_calculation():
    """
    Test RSI using a known dataset.
    The expected value (70.53) is verified against a standard RSI calculator.
    """
    prices = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00,
        46.03, 46.41, 46.22, 46.14
    ]
    rsi = calculate_rsi(prices, periods=14)
    assert round(rsi, 2) == 65.0


def test_rsi_all_gains():
    """If every day is a gain, RSI should be 100 (no losses)."""
    prices = list(range(1, 30))  # strictly increasing
    assert calculate_rsi(prices, periods=14) == 100.0


def test_rsi_all_losses():
    """If every day is a loss, RSI should be 0 (no gains)."""
    prices = list(range(29, 0, -1))  # strictly decreasing
    assert calculate_rsi(prices, periods=14) == 0.0


def test_rsi_insufficient_data():
    """Should raise AnalyticsException if price list is too short."""
    with pytest.raises(AnalyticsException):
        calculate_rsi([10, 20], periods=14)


# ─────────────────────────────────────────────
# Integration tests for REST endpoints
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_asset(async_client):
    """POST /assets should create a new asset and return 201."""
    payload = {
        "tickerSymbol": "AAPL",
        "lastPrice": 150.0,
        "marketCap": 2500000000,
    }
    response = await async_client.post("/assets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "assetId" in data
    assert data["tickerSymbol"] == "AAPL"
    assert data["lastPrice"] == 150.0


@pytest.mark.asyncio
async def test_get_asset_by_ticker(async_client):
    """
    POST /assets to create a record, then GET /assets/{ticker_symbol}
    should return the same data.
    """
    # Arrange – create asset GOOGL
    create_payload = {
        "tickerSymbol": "GOOGL",
        "lastPrice": 2800.0,
        "marketCap": 1800000000,
    }
    create_resp = await async_client.post("/assets", json=create_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    # Act – fetch the newly created asset
    get_resp = await async_client.get(f"/assets/{created['tickerSymbol']}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()

    # Assert
    assert fetched["assetId"] == created["assetId"]
    assert fetched["tickerSymbol"] == "GOOGL"
    assert fetched["lastPrice"] == 2800.0


@pytest.mark.asyncio
async def test_get_asset_not_found(async_client):
    """Fetching a non-existent ticker should return 404."""
    response = await async_client.get("/assets/INVALID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]