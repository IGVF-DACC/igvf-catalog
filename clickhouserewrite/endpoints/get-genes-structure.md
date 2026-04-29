# `GET /genes-structure`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/genes_structure.ts`](../../src/routers/datatypeRouters/nodes/genes_structure.ts)

## Description

Retrieve genes structure.<br>   you can filter by one of the four categories: gene, transcript, protein or region. <br>   Example: organism = Homo sapiens, <br>   region = chr1:212565300-212620800, <br>   gene_id = ENSG00000187642 (Ensembl ids), <br>   gene_name = ATF3, <br>   transcript_id = ENST00000443707 (Ensembl ids), <br>   transcript_id = TNF-207, <br>   type = exon, <br>   protein_id = ENSP00000305769, <br>   protein_name = SMAD1_HUMAN. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesStructure",
  "description": "Retrieve genes structure.<br>   you can filter by one of the four categories: gene, transcript, protein or region. <br>   Example: organism = Homo sapiens, <br>   region = chr1:212565300-212620800, <br>   gene_id = ENSG00000187642 (Ensembl ids), <br>   gene_name = ATF3, <br>   transcript_id = ENST00000443707 (Ensembl ids), <br>   transcript_id = TNF-207, <br>   type = exon, <br>   protein_id = ENSP00000305769, <br>   protein_name = SMAD1_HUMAN. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "gene_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "gene_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "transcript_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "transcript_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "protein_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "protein_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "region",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "CDS",
          "UTR",
          "exon",
          "intron",
          "start_codon",
          "stop_codon"
        ]
      }
    },
    {
      "name": "organism",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Mus musculus",
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
      }
    },
    {
      "name": "page",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number",
        "default": 0
      }
    },
    {
      "name": "limit",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number"
      }
    }
  ],
  "responses": {
    "200": {
      "description": "Successful response",
      "content": {
        "application/json": {
          "schema": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "_id": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                },
                "chr": {
                  "type": "string"
                },
                "start": {
                  "type": "number",
                  "nullable": true
                },
                "end": {
                  "type": "number",
                  "nullable": true
                },
                "strand": {
                  "type": "string"
                },
                "type": {
                  "type": "string"
                },
                "gene_id": {
                  "type": "string"
                },
                "gene_name": {
                  "type": "string"
                },
                "transcript_id": {
                  "type": "string"
                },
                "transcript_name": {
                  "type": "string"
                },
                "protein_id": {
                  "type": "string",
                  "nullable": true
                },
                "exon_number": {
                  "type": "string"
                },
                "exon_id": {
                  "type": "string",
                  "nullable": true
                },
                "organism": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "version": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                }
              },
              "required": [
                "_id",
                "name",
                "chr",
                "start",
                "end",
                "strand",
                "type",
                "gene_id",
                "gene_name",
                "transcript_id",
                "transcript_name",
                "exon_number",
                "exon_id",
                "organism",
                "source",
                "version",
                "source_url"
              ],
              "additionalProperties": false
            }
          }
        }
      }
    },
    "default": {
      "$ref": "#/components/responses/error"
    }
  }
}
```

## Implementation notes

_(none yet)_
