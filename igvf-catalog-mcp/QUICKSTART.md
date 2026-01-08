# Quick Start Guide

## Installation

1. Navigate to the MCP server directory:
```bash
cd igvf-catalog-mcp
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

## Running the Server

### Development/Local Testing
Point to your local IGVF Catalog API:
```bash
export IGVF_CATALOG_API_URL=http://localhost:2023
python -m igvf_catalog_mcp.server
```

### Production
Use the production API (default):
```bash
python -m igvf_catalog_mcp.server
```

## Running Tests

```bash
pytest
```

Run with coverage:
```bash
pytest --cov=igvf_catalog_mcp --cov-report=html
```

## Tools Overview

### 1. get_entity
Universal entity lookup with automatic type detection.

**Example queries:**
- `{"id": "BRCA1"}` - Gene by symbol
- `{"id": "ENSG00000139618"}` - Gene by Ensembl ID
- `{"id": "rs80357906"}` - Variant by rsID
- `{"id": "NC_000017.11:43044295:G:A"}` - Variant by SPDI
- `{"id": "ENSP00000493376"}` - Protein by Ensembl ID

### 2. search_region
Find entities within a genomic region.

**Example queries:**
- `{"region": "chr17:41M-42M"}` - Million notation
- `{"region": "chr1:1000000-2000000"}` - Standard format
- `{"region": "1:1,000,000-2,000,000"}` - With commas
- `{"region": "chr17:41M-42M", "include": ["genes"], "limit": 50}`

### 3. find_associations
Discover relationships between entities.

**Example queries:**
- `{"entity_id": "TP53", "relationship": "regulatory"}` - eQTLs for TP53
- `{"entity_id": "rs12345", "relationship": "genetic"}` - GWAS hits
- `{"entity_id": "ENSP00000493376", "relationship": "physical"}` - Protein interactions
- `{"entity_id": "BRCA1", "relationship": "all"}` - All relationship types

### 4. resolve_id
Convert between identifier formats.

**Example queries:**
- `{"id": "rs80357906"}` - Get SPDI, HGVS, coordinates
- `{"id": "BRCA1"}` - Get all gene identifiers and synonyms
- `{"id": "NC_000017.11:43044295:G:A"}` - Get rsID and other formats

### 5. list_sources
Discover available data sources.

**Example queries:**
- `{"category": "gene_expression"}` - eQTL sources
- `{"category": "regulatory"}` - Enhancer/TFBS sources
- `{}` - All categories

## Resources

The server provides read-only resources:
- `igvf://schemas/gene` - Gene entity schema
- `igvf://schemas/variant` - Variant entity schema
- `igvf://guide/identifiers` - ID format guide
- `igvf://examples/queries` - Example queries

## Configuration

Environment variables:
- `IGVF_CATALOG_API_URL` - API base URL (default: https://api.catalog.igvf.org)

## Architecture

```
igvf-catalog-mcp/
├── src/igvf_catalog_mcp/
│   ├── server.py          # MCP server entry point
│   ├── tools/             # 5 MCP tools
│   │   ├── get_entity.py
│   │   ├── search_region.py
│   │   ├── find_associations.py
│   │   ├── resolve_id.py
│   │   └── list_sources.py
│   ├── services/          # Core services
│   │   ├── api_client.py  # Async HTTP client
│   │   ├── id_parser.py   # ID type detection
│   │   ├── region_parser.py
│   │   └── formatter.py
│   └── resources/         # MCP resources
│       └── schemas.py
└── tests/                 # pytest tests
```

## Troubleshooting

### Connection Issues
- Verify the API URL is accessible
- Check firewall/network settings
- Ensure the IGVF Catalog API is running (if using local)

### ID Not Recognized
- Check the identifier format guide: `igvf://guide/identifiers`
- Use the `hint` parameter in `get_entity`
- Verify the entity type is supported

### No Results
- Check if filters are too restrictive
- Verify the entity exists in the database
- Try increasing the `limit` parameter

## Support

For issues or questions:
- IGVF Catalog API: https://api.catalog.igvf.org
- GitHub issues: https://github.com/IGVF-DACC/igvfd/issues
