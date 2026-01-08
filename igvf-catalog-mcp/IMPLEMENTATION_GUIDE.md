# IGVF Catalog MCP Server - Implementation Guide

> **Purpose**: This document provides context for LLMs continuing development of this MCP server.

## Project Overview

This is an MCP (Model Context Protocol) server that provides LLM-friendly access to the IGVF Catalog genomics knowledge graph API. The IGVF Catalog is built on ArangoDB and exposed via a tRPC/Express server with both REST (`/api/*`) and RPC (`/trpc/*`) interfaces.

### Why MCP?

The raw API has 60+ endpoints with complex parameter combinations. LLMs struggle with:
- Memorizing long enum lists (data sources, chromosomes, etc.)
- Exact ID format requirements
- Deep nested parameters
- Choosing between similar endpoints

This MCP server provides **intent-based semantic tools** that abstract away complexity.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (Python)                       │
├─────────────────────────────────────────────────────────────┤
│  Tools                    │  Resources                       │
│  ├── get_entity          │  ├── schemas (entity definitions)│
│  ├── search_region       │  └── id_guide (format examples)  │
│  ├── find_associations   │                                   │
│  ├── resolve_id          │                                   │
│  └── list_sources        │                                   │
├─────────────────────────────────────────────────────────────┤
│  Services                                                    │
│  ├── IDParser      (auto-detect entity type from ID)        │
│  ├── RegionParser  (normalize "chr1:1M-2M" formats)         │
│  ├── APIClient     (httpx async client)                     │
│  └── Formatter     (standardize responses)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              IGVF Catalog REST API                           │
│              http://localhost:8000/api/*                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Python over TypeScript
The team has more Python expertise. The MCP Python SDK is mature and well-documented.

### 2. Intent-Based Tools (not 1:1 endpoint mapping)
Instead of 60+ tools for each endpoint, we have 5 semantic tools:
- `get_entity` - Fetch any entity by ID (auto-detects type)
- `search_region` - Find entities in a genomic region
- `find_associations` - Query relationships (gene→variants, etc.)
- `resolve_id` - Translate between ID systems
- `list_sources` - Discover available data sources

### 3. Smart ID Parsing
The `IDParser` auto-detects entity types from identifiers:
- `ENSG00000139618` → gene (gene_id parameter)
- `rs12345` → variant (rsid parameter)
- `BRCA1` → gene (gene_name parameter)
- `P49711` → protein (protein_id parameter)

### 4. Flexible Region Input
The `RegionParser` normalizes various formats:
- `chr1:1000000-2000000` → standard
- `chr1:1M-2M` → `chr1:1000000-2000000`
- `1:1000000-2000000` → `chr1:1000000-2000000`

### 5. No LLM-Query Endpoint
The `/llm-query` endpoint in the main API is experimental and excluded from this MCP server.

## File Structure

```
igvf-catalog-mcp/
├── pyproject.toml              # Dependencies: mcp, httpx, pydantic
├── README.md                   # User-facing documentation
├── QUICKSTART.md               # Setup instructions
├── CHANGELOG.md                # Version history
├── IMPLEMENTATION_GUIDE.md     # This file (LLM handoff)
├── .gitignore
├── src/igvf_catalog_mcp/
│   ├── __init__.py
│   ├── server.py               # Main MCP server entry point
│   ├── services/
│   │   ├── __init__.py
│   │   ├── id_parser.py        # IDParser class
│   │   ├── region_parser.py    # RegionParser class
│   │   ├── api_client.py       # IGVFCatalogAPIClient (httpx)
│   │   └── formatter.py        # Response formatting (placeholder)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── get_entity.py       # get_entity tool
│   │   ├── search_region.py    # search_region tool
│   │   ├── find_associations.py # find_associations tool
│   │   ├── resolve_id.py       # resolve_id tool
│   │   └── list_sources.py     # list_sources tool
│   └── resources/
│       ├── __init__.py
│       └── schemas.py          # MCP resources (placeholder)
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_id_parser.py       # IDParser tests
    ├── test_region_parser.py   # RegionParser tests
    ├── test_api_client.py      # API client tests
    └── test_tools/
        └── __init__.py
```

## Implementation Status

### ✅ Completed

1. **Project Structure** - Full Python package with pyproject.toml
2. **IDParser** - Pattern matching for all major ID types
3. **RegionParser** - Handles chr prefix, M/K suffixes, validation
4. **APIClient** - Async httpx client with error handling
5. **Tool Skeletons** - All 5 tools have basic structure
6. **Unit Tests** - Core services have test coverage
7. **Documentation** - README, QUICKSTART, CHANGELOG

### 🔄 Partially Complete

1. **Tool Implementations** - Basic structure exists but needs:
   - Full parameter validation
   - Response formatting
   - Error message improvements
   - Integration with all relevant endpoints

2. **MCP Resources** - `schemas.py` is a placeholder, needs:
   - Entity schema definitions
   - ID format guide resource
   - Example queries

3. **Formatter Service** - Placeholder, needs:
   - Response truncation for large results
   - Field selection logic
   - LLM-friendly formatting

### ❌ Not Started

1. **Integration Tests** - Against live API
2. **MCP Server Registration** - Cursor/Claude Desktop config
3. **Caching** - For frequently requested data
4. **Rate Limiting** - Client-side throttling

## Critical Implementation Details

### IDParser Gene Symbol Fix (Recent)

**Issue**: Gene symbols like "BRCA1" were mapped to parameter `name`, but edge endpoints (`/genes/variants`, `/variants/genes`) expect `gene_name`.

**Fix**: Changed line 58 in `id_parser.py`:
```python
# Before (broken for edge endpoints)
(r'^[A-Z][A-Z0-9]{1,9}$', 'gene', 'name')

# After (works for all endpoints)
(r'^[A-Z][A-Z0-9]{1,9}$', 'gene', 'gene_name')
```

### API Base URL

Default: `http://localhost:8000` (configurable via `IGVF_CATALOG_API_URL` env var)

Production: `https://api.catalog.igvf.org` (verify this URL)

### Key API Endpoints

Node endpoints (single entity queries):
- `/api/genes` - Query by gene_id, gene_name, hgnc, region
- `/api/variants` - Query by rsid, spdi, hgvs, region
- `/api/proteins` - Query by protein_id
- `/api/ontology-terms` - Query by term_id

Edge endpoints (relationships):
- `/api/genes/variants` - Gene to variant associations
- `/api/variants/genes` - Variant to gene associations (QTLs, etc.)
- `/api/variants/phenotypes` - GWAS associations
- `/api/genes/pathways` - Pathway membership

### Common Query Parameters

Most endpoints accept:
- `page` (default: 0)
- `limit` (default: 25, max varies)
- `source` - Filter by data source
- `verbose` - Include full details (default: false for edge endpoints)

Region-based endpoints accept:
- `region` - Format: `chr1:1000000-2000000`
- `chr` + `start` + `end` - Alternative to region string

## Testing

```bash
cd igvf-catalog-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run specific test file
pytest tests/test_id_parser.py -v

# Run with coverage
pytest --cov=src/igvf_catalog_mcp
```

## Running the MCP Server

```bash
# Development
python -m igvf_catalog_mcp.server

# With custom API URL
IGVF_CATALOG_API_URL=https://api.catalog.igvf.org python -m igvf_catalog_mcp.server
```

## Key Files in Parent Repo to Reference

When understanding the API structure, these files are essential:

1. **`src/routers/_app.ts`** - Main router aggregation
2. **`src/routers/datatypeRouters/descriptions.ts`** - Endpoint descriptions (very useful!)
3. **`src/routers/datatypeRouters/nodes/*.ts`** - Node endpoint implementations
4. **`src/routers/datatypeRouters/edges/*.ts`** - Edge endpoint implementations
5. **`src/routers/datatypeRouters/params.ts`** - Common parameter definitions
6. **`src/routers/datatypeRouters/_helpers.ts`** - Query building helpers
7. **`data/schemas/`** - JSON schemas for all collections

## Next Steps (Priority Order)

1. **Complete find_associations tool** - Most complex, handles all edge queries
2. **Implement response formatting** - Truncate large results, select fields
3. **Add MCP resources** - Schema definitions, ID format guide
4. **Integration testing** - Test against running API
5. **Documentation** - Add example queries to README
6. **MCP registration** - Create config for Cursor/Claude Desktop

## Gotchas & Warnings

1. **Gene symbol ambiguity**: Short uppercase strings like "ABC" could be gene symbols OR other things. The parser assumes gene if pattern matches.

2. **Ontology term separators**: API expects underscores (`MONDO_0008199`) but users may use colons (`MONDO:0008199`). The IDParser normalizes this.

3. **Region chromosome prefix**: API requires `chr` prefix. Users may omit it. RegionParser handles this.

4. **Verbose parameter**: Edge endpoints return minimal data by default. Set `verbose=true` for full details (but larger responses).

5. **Pagination**: API uses 0-indexed pages. Default limit is 25.

## Contact & Resources

- **IGVF Catalog API Docs**: Swagger UI at API root (e.g., `http://localhost:8000/`)
- **MCP SDK Docs**: https://modelcontextprotocol.io/
- **Parent Repo**: This folder is in `igvf-catalog/igvf-catalog-mcp/`

---

*Last updated: January 2026*
*Created during initial MCP server implementation*
