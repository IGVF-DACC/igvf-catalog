# `GET /transcripts`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/transcripts.ts`](../../src/routers/datatypeRouters/nodes/transcripts.ts)

## Description

Retrieve transcripts. <br>   Example: region = chr20:9537369-9839076, <br>   transcript_type = protein_coding, <br>   transcript_id = ENST00000443707 (Ensembl ids). <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "transcripts",
  "description": "Retrieve transcripts. <br>   Example: region = chr20:9537369-9839076, <br>   transcript_type = protein_coding, <br>   transcript_id = ENST00000443707 (Ensembl ids). <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "transcript_id",
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
      "name": "transcript_type",
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
          "non_stop_decay",
          "nonsense_mediated_decay",
          "processed_pseudogene",
          "processed_transcript",
          "protein_coding",
          "protein_coding_CDS_not_defined",
          "protein_coding_LoF",
          "pseudogene",
          "rRNA",
          "rRNA_pseudogene",
          "retained_intron",
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
            "anyOf": [
              {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "transcript_type": {
                      "type": "string"
                    },
                    "chr": {
                      "type": "string"
                    },
                    "start": {
                      "type": "number"
                    },
                    "end": {
                      "type": "number"
                    },
                    "strand": {
                      "type": "string"
                    },
                    "name": {
                      "type": "string"
                    },
                    "gene_name": {
                      "type": "string"
                    },
                    "MANE_Select": {
                      "type": "boolean",
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
                    }
                  },
                  "required": [
                    "_id",
                    "transcript_type",
                    "chr",
                    "start",
                    "end",
                    "strand",
                    "name",
                    "gene_name",
                    "source",
                    "version",
                    "source_url"
                  ],
                  "additionalProperties": false
                }
              },
              {
                "type": "object",
                "properties": {
                  "_id": {
                    "type": "string"
                  },
                  "transcript_type": {
                    "type": "string"
                  },
                  "chr": {
                    "type": "string"
                  },
                  "start": {
                    "type": "number"
                  },
                  "end": {
                    "type": "number"
                  },
                  "strand": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  },
                  "gene_name": {
                    "type": "string"
                  },
                  "MANE_Select": {
                    "type": "boolean",
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
                  }
                },
                "required": [
                  "_id",
                  "transcript_type",
                  "chr",
                  "start",
                  "end",
                  "strand",
                  "name",
                  "gene_name",
                  "source",
                  "version",
                  "source_url"
                ],
                "additionalProperties": false
              }
            ]
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
