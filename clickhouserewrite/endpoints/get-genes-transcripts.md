# `GET /genes/transcripts`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts)

## Description

Retrieve transcripts from genes.<br>     Set verbose = true to retrieve full info on the transcripts.<br>     Example: gene_name = ATF3, hgnc_id = HGNC:28208, <br>     alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids). <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "transcriptsFromGenes",
  "description": "Retrieve transcripts from genes.<br>     Set verbose = true to retrieve full info on the transcripts.<br>     Example: gene_name = ATF3, hgnc_id = HGNC:28208, <br>     alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids). <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.",
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
      "name": "gene_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "alias",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
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
      "name": "verbose",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "true",
          "false"
        ],
        "default": "false"
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
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "version": {
                  "type": "string"
                },
                "gene": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
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
                  ]
                },
                "transcript": {
                  "anyOf": [
                    {
                      "type": "string"
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
                },
                "name": {
                  "type": "string"
                }
              },
              "required": [
                "name"
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
