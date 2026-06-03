import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code in (200, 404)
