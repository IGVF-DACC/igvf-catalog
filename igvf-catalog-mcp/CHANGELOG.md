# Changelog

## [Unreleased]

### Fixed
- **ID Parser gene symbol parameter**: Changed gene symbol detection to return `"gene_name"` instead of `"name"` as the parameter name. This ensures compatibility with edge endpoints (e.g., `/api/genes/variants`, `/api/variants/genes`) which expect `gene_name`, while maintaining compatibility with node endpoints (e.g., `/api/genes`) which accept both `name` and `gene_name`. This fix resolves issues where `find_associations` tool would fail when querying relationships for gene symbols like "TP53" or "BRCA1".

## [0.1.0] - Initial Release

### Added
- Complete MCP server implementation with 5 tools
- Smart entity lookup with auto-detection for 30+ ID patterns
- Flexible genomic region parsing (supports M/K notation, commas, etc.)
- Async API client with httpx
- Comprehensive test suite
- MCP resources for schemas and guides
