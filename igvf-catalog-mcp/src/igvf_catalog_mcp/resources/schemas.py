"""MCP resources for entity schemas."""

from mcp.types import Resource, TextContent

# Gene schema
GENE_SCHEMA = Resource(
    uri='igvf://schemas/gene',
    name='Gene Entity Schema',
    mimeType='application/json',
    description='Schema and field descriptions for gene entities',
)

GENE_SCHEMA_CONTENT = """
{
  "entity_type": "gene",
  "description": "Protein-coding and non-coding genes from GENCODE",
  "fields": {
    "_id": "Gene ID (Ensembl format: ENSG*)",
    "chr": "Chromosome (e.g., 'chr1', 'chrX')",
    "start": "Start position (0-based, GRCh38/GRCm39)",
    "end": "End position (0-based, half-open)",
    "name": "Gene symbol (e.g., 'BRCA1', 'TP53')",
    "gene_type": "Type of gene (protein_coding, lncRNA, miRNA, etc.)",
    "strand": "Strand (+/-)",
    "hgnc": "HGNC ID (e.g., 'HGNC:1100')",
    "entrez": "Entrez Gene ID (e.g., 'ENTREZ:672')",
    "synonyms": "List of gene name aliases",
    "collections": "Gene collections (ACMG73, GREGoR, etc.)",
    "study_sets": "Associated study sets",
    "source": "Data source (GENCODE)",
    "version": "GENCODE version",
    "organism": "Homo sapiens or Mus musculus"
  }
}
"""

# Variant schema
VARIANT_SCHEMA = Resource(
    uri='igvf://schemas/variant',
    name='Variant Entity Schema',
    mimeType='application/json',
    description='Schema and field descriptions for genetic variants',
)

VARIANT_SCHEMA_CONTENT = """
{
  "entity_type": "variant",
  "description": "Genetic variants from FAVOR, dbSNP, and other sources",
  "fields": {
    "_id": "Internal variant ID (NC_*:pos:ref:alt format)",
    "chr": "Chromosome (e.g., 'chr1')",
    "pos": "Position (0-based, GRCh38)",
    "ref": "Reference allele",
    "alt": "Alternate allele",
    "rsid": "dbSNP rsID (e.g., 'rs12345')",
    "spdi": "SPDI format (NC_000001.11:12345:A:G)",
    "hgvs": "HGVS format (NC_000001.11:g.12346A>G)",
    "ca_id": "ClinGen Allele Registry ID (e.g., 'CA12345')",
    "annotations": {
      "bravo_af": "Allele frequency in BRAVO",
      "gnomad_af_*": "gnomAD allele frequencies by population",
      "cadd_phred": "CADD phred score",
      "GENCODE_category": "coding or noncoding"
    },
    "organism": "Homo sapiens or Mus musculus"
  },
  "coordinate_system": "0-based, half-open intervals"
}
"""

# Identifier guide
IDENTIFIER_GUIDE = Resource(
    uri='igvf://guide/identifiers',
    name='Identifier Format Guide',
    mimeType='text/markdown',
    description='How to recognize and format different ID types',
)

IDENTIFIER_GUIDE_CONTENT = """
# Identifier Format Guide

## Genes
- **Ensembl**: ENSG00000139618 (starts with ENSG)
- **Gene Symbol**: BRCA1, TP53 (2-10 uppercase letters/numbers)
- **HGNC**: HGNC:1100 (HGNC:digits)
- **Entrez**: ENTREZ:672 or just 672

## Variants
- **rsID**: rs12345 (starts with 'rs')
- **SPDI**: NC_000001.11:12345:A:G (RefSeq:pos:ref:alt)
- **HGVS**: NC_000001.11:g.12346A>G (RefSeq:g.pos ref>alt)
- **ClinGen**: CA12345 (starts with 'CA')

## Proteins
- **Ensembl**: ENSP00000493376 (starts with ENSP)
- **UniProt**: P49711, P49711-2 (6 alphanumeric + optional -isoform)

## Transcripts
- **Ensembl**: ENST00000443707 (starts with ENST)

## Ontology Terms
- **Disease**: Orphanet_586, MONDO_0008199, DOID_0050741
- **Cell Type**: CL_0000084
- **Tissue**: UBERON_0002048
- **Phenotype**: EFO_0000400, OBA_0000128
- **Gene Ontology**: GO_0008150

## Other
- **Drug**: PA448497 (PharmGKB)
- **Complex**: CPX-9 (Complex Portal)
- **Pathway**: R-HSA-164843 (Reactome)
- **Study**: GCST007798 (GWAS Catalog)

## Coordinate System
The IGVF Catalog uses **0-based, half-open** coordinates:
- Start is inclusive (0-based)
- End is exclusive
- Example: chr1:100-200 includes positions 100-199
"""

# Example queries
EXAMPLE_QUERIES = Resource(
    uri='igvf://examples/queries',
    name='Example Queries',
    mimeType='text/markdown',
    description='Common query patterns with expected results',
)

EXAMPLE_QUERIES_CONTENT = """
# Example Queries

## 1. Look up a gene by symbol
```json
Tool: get_entity
Input: {"id": "BRCA1"}
Returns: Gene information including coordinates, HGNC ID, Ensembl ID
```

## 2. Find variants in a region
```json
Tool: search_region
Input: {"region": "chr17:41000000-42000000"}
Returns: Genes, variants, and regulatory elements in the region
```

## 3. Find eQTLs for a gene
```json
Tool: find_associations
Input: {"entity_id": "TP53", "relationship": "regulatory"}
Returns: Variants that affect TP53 expression (eQTLs, sQTLs)
```

## 4. Convert variant ID formats
```json
Tool: resolve_id
Input: {"id": "rs80357906"}
Returns: SPDI, HGVS, ClinGen ID, and genomic coordinates
```

## 5. Find GWAS associations for a variant
```json
Tool: find_associations
Input: {"entity_id": "rs12345", "relationship": "genetic"}
Returns: Phenotypes/diseases associated with the variant
```

## 6. Discover available data sources
```json
Tool: list_sources
Input: {"category": "gene_expression"}
Returns: GTEx, AFGR, EBI eQTL Catalogue details
```

## 7. Find protein-protein interactions
```json
Tool: find_associations
Input: {"entity_id": "ENSP00000493376", "relationship": "physical"}
Returns: Interacting proteins from BioGRID
```

## 8. Flexible region formats
All these work:
- chr1:1000000-2000000
- 1:1000000-2000000
- chr1:1,000,000-2,000,000
- chrX:1M-2M
- chr1:1.5M-2.5M
"""


async def get_resource_content(uri: str) -> str:
    """Get the content for a resource URI."""
    resource_map = {
        'igvf://schemas/gene': GENE_SCHEMA_CONTENT,
        'igvf://schemas/variant': VARIANT_SCHEMA_CONTENT,
        'igvf://guide/identifiers': IDENTIFIER_GUIDE_CONTENT,
        'igvf://examples/queries': EXAMPLE_QUERIES_CONTENT,
    }

    content = resource_map.get(uri)
    if content is None:
        raise ValueError(f'Unknown resource URI: {uri}')

    return content.strip()


# All resources
ALL_RESOURCES = [
    GENE_SCHEMA,
    VARIANT_SCHEMA,
    IDENTIFIER_GUIDE,
    EXAMPLE_QUERIES,
]
