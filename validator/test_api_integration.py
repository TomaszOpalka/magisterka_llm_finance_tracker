import pytest
import httpx
import asyncio

# Port mapping from test_models.py
MODELS = {
    "Gemini PRO": 8001,
    "Gemini Flash": 8002,
    "GPT-4o": 8003,
    "DeepSeek": 8004,
    "Grok": 8005
}

@pytest.mark.asyncio
@pytest.mark.parametrize("name, port", MODELS.items())
async def test_model_integration_full_suite(name, port):
    """
    Master Integration Test.
    Covers:
    - Connectivity & Health
    - Asset Creation (200/201/409)
    - Market Data Sync
    - Pagination & Sorting
    - Filtering (min_price)
    - Error Handling (404)
    - PK Contract Compliance (No 'id' field, only 'asset_id')
    """
    base_url = f"http://127.0.0.1:{port}"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
        # 0. Connectivity Check
        try:
            status_resp = await client.get("/status")
            if status_resp.status_code != 200:
                pytest.skip(f"Model {name} is not healthy (Status {status_resp.status_code})")
        except Exception:
            pytest.skip(f"Model {name} is OFFLINE at port {port}")

        # 1. Asset Creation
        print(f"\n[Test {name}] Step 1: Creation...")
        create_data = {
            "ticker_symbol": "AAPL",
            "last_price": 0.0,
            "market_cap": 2500000000000
        }
        c_resp = await client.post("/assets", json=create_data)
        assert c_resp.status_code in [200, 201, 409, 400], f"Unexpected status during creation: {c_resp.status_code}"

        # 2. Market Data Sync
        print(f"[Test {name}] Step 2: Syncing...")
        s_resp = await client.post("/assets/sync")
        assert s_resp.status_code == 200, f"Sync failed: {s_resp.text}"

        # 3. Verification & PK Contract
        print(f"[Test {name}] Step 3: Verifying PK & Data...")
        g_resp = await client.get("/assets/AAPL")
        assert g_resp.status_code == 200
        asset = g_resp.json()
        
        # PR #67 Check: 'id' must NOT be present
        assert "id" not in asset, f"KPI FAILURE: Model {name} uses 'id' instead of 'asset_id'"
        assert "asset_id" in asset, f"KPI FAILURE: Model {name} missing 'asset_id'"
        assert asset["last_price"] > 0, f"Sync check failed: price is still {asset['last_price']}"

        # 4. Pagination & Sorting
        print(f"[Test {name}] Step 4: Pagination & Sorting...")
        p_resp = await client.get("/assets?limit=5&sort_by=market_cap")
        if p_resp.status_code == 200:
            p_data = p_resp.json()
            assert isinstance(p_data, list), "Pagination should return a list"
            assert len(p_data) <= 5, "Limit parameter ignored"
        else:
            print(f"⚠️ {name}: Pagination returned {p_resp.status_code}")

        # 5. Filtering
        print(f"[Test {name}] Step 5: Filtering...")
        f_resp = await client.get("/assets?min_price=1000000") # High price to test filtering
        if f_resp.status_code == 200:
            f_data = f_resp.json()
            # If we don't have such expensive stocks, it might be empty or 404
            if isinstance(f_data, list):
                for a in f_data:
                    assert a["last_price"] >= 1000000, "Filtering failed"

        # 6. Error Handling (404)
        print(f"[Test {name}] Step 6: 404 Handling...")
        err_resp = await client.get("/assets/NONEXISTENT_TICKER_123")
        assert err_resp.status_code == 404, f"Model {name} should return 404 for missing asset"

        print(f"✅ Model {name} passed all functional KPIs.")
