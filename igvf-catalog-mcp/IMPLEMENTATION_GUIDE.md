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
│  ├── find_ld (NEW)       │                                   │
│  ├── resolve_id          │                                   │
│  └── list_sources        │                                   │
├─────────────────────────────────────────────────────────────┤
│  Services                                                    │
│  ├── IDParser      (auto-detect entity type from ID)        │
│  ├── RegionParser  (normalize "chr1:1M-2M" formats)         │
│  ├── EdgeConfig    (NEW: endpoint parameter mapping)        │
│  ├── APIClient     (httpx async client)                     │
│  └── Formatter     (standardize responses)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              IGVF Catalog REST API                           │
│              https://api.catalogkg.igvf.org/api/*            │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Python over TypeScript
The team has more Python expertise. The MCP Python SDK is mature and well-documented.

### 2. Intent-Based Tools (not 1:1 endpoint mapping)
Instead of 60+ tools for each endpoint, we have 6 semantic tools:
- `get_entity` - Fetch any entity by ID (auto-detects type)
- `search_region` - Find entities in a genomic region
- `find_associations` - Query relationships (gene→variants, diseases, etc.)
- `find_ld` - Find variants in linkage disequilibrium (specialized tool)
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
│   │   ├── edge_config.py      # NEW: Edge endpoint configuration
│   │   ├── api_client.py       # IGVFCatalogAPIClient (httpx)
│   │   └── formatter.py        # Response formatting (placeholder)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── get_entity.py       # get_entity tool
│   │   ├── search_region.py    # search_region tool
│   │   ├── find_associations.py # find_associations tool (UPDATED)
│   │   ├── find_ld.py          # NEW: find_ld tool for LD queries
│   │   ├── resolve_id.py       # resolve_id tool
│   │   └── list_sources.py     # list_sources tool (UPDATED)
│   └── resources/
│       ├── __init__.py
│       └── schemas.py          # MCP resources (placeholder)
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_id_parser.py       # IDParser tests
    ├── test_region_parser.py   # RegionParser tests
    ├── test_api_client.py      # API client tests
    ├── test_edge_config.py     # NEW: Edge config tests
    └── test_tools/
        └── __init__.py
```

## Implementation Status

### ✅ Completed

1. **Project Structure** - Full Python package with pyproject.toml
2. **IDParser** - Pattern matching for all major ID types (including gene_name fix)
3. **RegionParser** - Handles chr prefix, M/K suffixes, validation
4. **EdgeConfig** - Centralized edge endpoint configuration system (NEW)
5. **APIClient** - Async httpx client with error handling
6. **Tool Implementations** - All 6 tools fully implemented:
   - `get_entity` - Complete with auto-detection
   - `search_region` - Complete with flexible region parsing
   - `find_associations` - Complete with edge config integration
   - `find_ld` - Complete LD-specific tool
   - `resolve_id` - Complete ID translation
   - `list_sources` - Complete with accurate source data
7. **Unit Tests** - Core services have test coverage including edge config
8. **Documentation** - README, QUICKSTART, CHANGELOG, IMPLEMENTATION_GUIDE

### 🔄 Partially Complete

1. **MCP Resources** - `schemas.py` is a placeholder, needs:
   - Entity schema definitions
   - ID format guide resource
   - Example queries

2. **Formatter Service** - Placeholder, needs:
   - Response truncation for large results
   - Field selection logic
   - LLM-friendly formatting

### ❌ Not Started

1. **Integration Tests** - Against live API
2. **MCP Server Registration** - Cursor/Claude Desktop config
3. **Caching** - For frequently requested data
4. **Rate Limiting** - Client-side throttling

## Edge Configuration System (Recent Enhancement)

### Overview

The edge configuration system (`services/edge_config.py`) provides a centralized registry of all edge (relationship) endpoints in the IGVF Catalog API. This solves a critical problem: different endpoints expect different parameter names for the same entity type.

### The Problem It Solves

Before the edge config:
- `IDParser` would return `gene_name` for "BRCA1"
- But endpoint `/genes/variants` might expect `gene_name` while `/variants/genes` expects it too
- Source enums were hardcoded and often incorrect ("GTEx" instead of "EBI eQTL Catalogue")
- Filter parameters varied by endpoint but weren't validated

### Architecture

```python
EDGE_ENDPOINTS = {
    "variants_genes": {
        "path": "/api/variants/genes",
        "from_type": "variant",
        "to_type": "gene",
        "from_params": ["variant_id", "spdi", "hgvs", "rsid", "ca_id"],
        "sources": ["AFGR", "EBI eQTL Catalogue", "IGVF"],
        "labels": ["eQTL", "splice_QTL"],
        "filters": {
            "log10pvalue": "range",
            "effect_size": "range",
            "biological_context": "string"
        },
        "supports_verbose": True,
        "max_limit": 500
    },
    # ... 30+ more endpoints
}
```

### Key Features

1. **Parameter Validation** - Each endpoint declares which parameters it accepts
2. **Source Accuracy** - Sources are pulled from actual API implementation
3. **Filter Mapping** - Filters are type-aware (range vs string vs enum)
4. **Relationship Abstraction** - High-level relationship types map to specific endpoints

### Relationship Type Mapping

```python
RELATIONSHIP_TYPE_MAPPING = {
    'regulatory': {
        'variant': ['variants_genes', 'variants_genomic_elements'],
        'gene': ['genes_variants', 'genomic_elements_genes']
    },
    'genetic': {
        'variant': ['variants_phenotypes', 'variants_diseases']
    },
    'ld': {
        'variant': ['variants_variants']
    },
    # ... more types
}
```

This allows `find_associations(entity_id="TP53", relationship="regulatory")` to automatically query the correct endpoints.

### Benefits

- **Maintainability** - Single source of truth for endpoint configuration
- **Accuracy** - Sources and parameters match actual API requirements
- **Validation** - Tools can validate user inputs against endpoint constraints
- **Documentation** - Configuration serves as API documentation

## Critical Implementation Details

### IDParser Gene Symbol Fix

**Issue**: Gene symbols like "BRCA1" were mapped to parameter `name`, but edge endpoints (`/genes/variants`, `/variants/genes`) expect `gene_name`.

**Fix**: Changed line 58 in `id_parser.py`:
```python
# Before (broken for edge endpoints)
(r'^[A-Z][A-Z0-9]{1,9}$', 'gene', 'name')

# After (works for all endpoints)
(r'^[A-Z][A-Z0-9]{1,9}$', 'gene', 'gene_name')
```

### find_ld Tool (Specialized LD Queries)

**Purpose**: Linkage disequilibrium queries have unique parameters (r², D', ancestry) that don't fit well in the generic `find_associations` tool.

**Design Decision**: Created a dedicated `find_ld` tool with:
- Clear r² and D' threshold parameters
- Ancestry selection (AFR, AMR, EAS, EUR, SAS)
- Specialized summary statistics (strong/moderate/weak LD counts)
- Better UX than forcing users to understand range filters

**Usage Example**:
```python
find_ld(variant_id="rs12345", r2_threshold=0.8, ancestry="EUR")
```

This is clearer than:
```python
find_associations(entity_id="rs12345", relationship="ld", filters={"r2": "gte:0.8", "ancestry": "EUR"})
```

### API Base URL

Default: `https://api.catalogkg.igvf.org` (configurable via `IGVF_CATALOG_API_URL` env var)

Development: `http://localhost:8000` (when running API locally)

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

1. **Implement response formatting** - Truncate large results, select fields
2. **Add MCP resources** - Schema definitions, ID format guide
3. **Integration testing** - Test against live API
4. **Documentation** - Add example queries to README
5. **Performance optimization** - Caching, parallel queries
6. **Additional tools** - Consider adding:
   - `get_variants_by_frequency` - Specialized allele frequency queries
   - `find_coexpressed_genes` - Dedicated coexpression tool
   - `get_pathway_genes` - Pathway membership queries

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

*Last updated: January 8, 2026*
*Updated with edge configuration system, find_ld tool, and improved association queries*
