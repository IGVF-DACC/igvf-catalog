"""Async HTTP client for the IGVF Catalog API."""

import os
from typing import Any, Optional

import httpx


class IGVFCatalogClient:
    """Async HTTP client for querying the IGVF Catalog API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API. Defaults to production if not provided.
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or os.getenv(
            'IGVF_CATALOG_API_URL', 'https://api.catalogkg.igvf.org')).rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint path (e.g., "/api/genes")
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager.")

        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def get_entity(
        self,
        entity_type: str,
        param_name: str,
        param_value: str,
        additional_params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Get an entity by ID from the appropriate endpoint.

        Args:
            entity_type: Type of entity (gene, variant, etc.)
            param_name: Parameter name for the query (e.g., "gene_id")
            param_value: Value for the parameter
            additional_params: Additional query parameters

        Returns:
            List of entity objects (usually one, but can be multiple)
        """
        endpoint_map = {
            'gene': '/api/genes',
            'transcript': '/api/transcripts',
            'protein': '/api/proteins',
            'variant': '/api/variants',
            'ontology': '/api/ontology-terms',
            'drug': '/api/drugs',
            'complex': '/api/complexes',
            'study': '/api/studies',
            'pathway': '/api/pathways',
        }

        endpoint = endpoint_map.get(entity_type)
        if not endpoint:
            raise ValueError(f'Unknown entity type: {entity_type}')

        params = {param_name: param_value, 'page': 0}
        if additional_params:
            params.update(additional_params)

        result = await self.get(endpoint, params)

        # Handle different response formats
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            # Some endpoints wrap results in a dict
            return [result]
        else:
            return []

    async def search_region(
        self,
        endpoint: str,
        region_str: str,
        organism: str = 'Homo sapiens',
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """
        Search for entities in a genomic region.

        Args:
            endpoint: API endpoint to query
            region_str: Region string (e.g., "chr1:1000-2000")
            organism: Organism name
            limit: Maximum number of results

        Returns:
            List of entity objects
        """
        params = {
            'region': region_str,
            'organism': organism,
            'limit': limit,
            'page': 0,
        }

        result = await self.get(endpoint, params)
        return result if isinstance(result, list) else []

    async def find_associations(
        self,
        endpoint: str,
        params: dict[str, Any],
        verbose: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Find associations/relationships between entities.

        Args:
            endpoint: API endpoint for the relationship
            params: Query parameters
            verbose: Whether to return full entity objects

        Returns:
            List of association objects
        """
        query_params = {
            **params, 'verbose': 'true' if verbose else 'false', 'page': 0}
        result = await self.get(endpoint, query_params)
        return result if isinstance(result, list) else []
