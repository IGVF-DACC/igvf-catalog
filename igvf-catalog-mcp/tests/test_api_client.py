"""Tests for API client."""

import pytest
from igvf_catalog_mcp.services.api_client import IGVFCatalogClient


class TestIGVFCatalogClient:
    """Test API client functionality."""

    def test_client_initialization(self):
        """Test client initialization with default URL."""
        client = IGVFCatalogClient()
        assert 'catalog.igvf.org' in client.base_url
        assert client.timeout == 30.0

    def test_client_custom_url(self):
        """Test client initialization with custom URL."""
        client = IGVFCatalogClient(base_url='http://localhost:2023')
        assert client.base_url == 'http://localhost:2023'

    def test_client_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL."""
        client = IGVFCatalogClient(base_url='http://localhost:2023/')
        assert client.base_url == 'http://localhost:2023'

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager."""
        async with IGVFCatalogClient(base_url='http://localhost:2023') as client:
            assert client._client is not None

        # Client should be closed after context
        assert client._client is None or client._client.is_closed

    @pytest.mark.asyncio
    async def test_get_without_context_raises_error(self):
        """Test that get() raises error outside context manager."""
        client = IGVFCatalogClient()
        with pytest.raises(RuntimeError, match='Client not initialized'):
            await client.get('/api/genes')
