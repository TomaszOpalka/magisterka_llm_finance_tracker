"""
Unit and integration tests for Finance Track.
"""

import pytest
from httpx import AsyncClient

from experiments.mgr_gpt_free.analytics import (
    calculate_moving_average,
    calculate_rsi,
)


@pytest.mark.asyncio
async def test_calculate_moving_average():
    """
    Test simple moving average calculation.
    """
    prices = [10.0, 20.0, 30.0]

    result = calculate_moving_average(prices)

    assert result == 20.0


@pytest.mark.asyncio
async def test_calculate_moving_average_empty():
    """
    Test moving average with empty data.
    """
    result = calculate_moving_average([])

    assert result is None


@pytest.mark.asyncio
async def test_calculate_rsi():
    """
    Test RSI calculation.
    """
    prices = [
        44.34,
        44.09,
        44.15,
        43.61,
        44.33,
        44.83,
        45.10,
        45.42,
        45.84,
        46.08,
        45.89,
        46.03,
        45.61,
        46.28,
        46.28,
        46.00,
        46.03,
        46.41,
        46.22,
        45.64,
    ]

    result = calculate_rsi(prices)

    assert result is not None
    assert isinstance(result, float)
    assert 0 <= result <= 100


@pytest.mark.asyncio
async def test_calculate_rsi_insufficient_data():
    """
    Test RSI with insufficient data.
    """
    prices = [10.0, 11.0]

    result = calculate_rsi(prices)

    assert result is None


@pytest.mark.asyncio
async def test_create_and_get_asset(
    client: AsyncClient,
):
    """
    Integration test for asset creation and retrieval.
    """
    payload = {
        "tickerSymbol": "MSFT",
        "lastPrice": 150.0,
        "marketCap": 3000000000000,
        "lastUpdated": None,
    }

    # Create asset
    create_response = await client.post(
        "/assets",
        json=payload,
    )

    assert create_response.status_code == 201

    created_asset = create_response.json()

    assert created_asset["tickerSymbol"] == "MSFT"
    assert created_asset["assetId"] is not None
    assert created_asset["lastPrice"] == 150.0

    # Retrieve asset
    get_response = await client.get(
        "/assets/MSFT",
    )

    assert get_response.status_code == 200

    retrieved_asset = get_response.json()

    assert retrieved_asset["tickerSymbol"] == "MSFT"
    assert retrieved_asset["assetId"] == (
        created_asset["assetId"]
    )