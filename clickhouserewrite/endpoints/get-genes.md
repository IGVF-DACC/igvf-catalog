# `GET /genes`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/genes.ts`](../../src/routers/datatypeRouters/nodes/genes.ts)

## Description

Retrieve genes.<br>   Example: organism = Homo sapiens, <br>   name = SAMD1, <br>   region = chr1:212565300-212620800, <br>   synonym = CKLF, <br>   collection = ACMG73, <br>   study_set = MorPhiC, <br>   gene_id = ENSG00000187642 (Ensembl ids), <br>   gene_type = protein_coding, <br>   hgnc_id = HGNC:28208, <br>   entrez = ENTREZ:84808. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genes",
  "description": "Retrieve genes.<br>   Example: organism = Homo sapiens, <br>   name = SAMD1, <br>   region = chr1:212565300-212620800, <br>   synonym = CKLF, <br>   collection = ACMG73, <br>   study_set = MorPhiC, <br>   gene_id = ENSG00000187642 (Ensembl ids), <br>   gene_type = protein_coding, <br>   hgnc_id = HGNC:28208, <br>   entrez = ENTREZ:84808. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "hgnc_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "entrez",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "name",
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
      "name": "synonym",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "collection",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "ACMG73",
          "GREGoR",
          "Morphic",
          "StanfordFCC"
        ]
      }
    },
    {
      "name": "study_set",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "16p11.2 Deletion - Shendure",
          "Blood Master Regulators",
          "Cardiac - Engreitz",
          "Cardiac - Munshi",
          "Cardiac - Quertermous",
          "Cardiometabolic TFs",
          "Cardiomyopathies-Steinmetz",
          "CdLS-like phenotype",
          "Coronary Artery Disease - Lettre",
          "DiGeorge Syndrome - Park",
          "DiGeorge Syndrome - Shendure",
          "GREGoR Candidate - BCM",
          "GREGoR Candidate - Broad",
          "GREGoR Candidate - GSS",
          "GREGoR Candidate - UW",
          "IGVFFI6537JARB",
          "IGVFFI7781XWZY",
          "LDL-C uptake",
          "MorPhiC",
          "Pancreatic differentiation",
          "Pulmonary arterial hypertension - Rabinovitch",
          "SGE-Starita",
          "Strong Selection - Sunyaev",
          "VAMP-seq",
          "Williams Syndrome - Park",
          "Williams Syndrome - Shendure"
        ]
      }
    },
    {
      "name": "gene_type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "IG_C_gene",
          "IG_C_pseudogene",
          "IG_D_gene",
          "IG_J_gene",
          "IG_J_pseudogene",
          "IG_V_gene",
          "IG_V_pseudogene",
          "IG_pseudogene",
          "Mt_rRNA",
          "Mt_tRNA",
          "TEC",
          "TR_C_gene",
          "TR_D_gene",
          "TR_J_gene",
          "TR_J_pseudogene",
          "TR_V_gene",
          "TR_V_pseudogene",
          "artifact",
          "lncRNA",
          "miRNA",
          "misc_RNA",
          "processed_pseudogene",
          "protein_coding",
          "pseudogene",
          "rRNA",
          "rRNA_pseudogene",
          "ribozyme",
          "sRNA",
          "scRNA",
          "scaRNA",
          "snRNA",
          "snoRNA",
          "transcribed_processed_pseudogene",
          "transcribed_unitary_pseudogene",
          "transcribed_unprocessed_pseudogene",
          "translated_processed_pseudogene",
          "translated_unprocessed_pseudogene",
          "unitary_pseudogene",
          "unprocessed_pseudogene",
          "vault_RNA"
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
                "gene_type": {
                  "type": "string",
                  "nullable": true
                },
                "name": {
                  "type": "string"
                },
                "strand": {
                  "type": "string",
                  "nullable": true
                },
                "hgnc": {
                  "type": "string",
                  "nullable": true
                },
                "entrez": {
                  "type": "string",
                  "nullable": true
                },
                "collections": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "study_sets": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "version": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "synonyms": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "chr",
                "start",
                "end",
                "gene_type",
                "name",
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
