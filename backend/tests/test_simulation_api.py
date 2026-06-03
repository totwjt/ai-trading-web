"""
实盘模拟 API 集成测试

测试 /api/trading/simulations/ 相关端点
"""

import pytest
from httpx import ASGITransport, AsyncClient

# 直接导入 FastAPI app
from server import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_simulations(client: AsyncClient):
    response = await client.get("/api/trading/simulations/")
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert data["code"] == 0 or data["code"] == 0


@pytest.mark.asyncio
async def test_get_simulation_stats(client: AsyncClient):
    response = await client.get("/api/trading/simulations/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
