# `GET /genes/proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts)

## Description

Retrieve proteins from genes.<br>   Set verbose = true to retrieve full info on the proteins. <br>   Example: gene_name = ATF3, <br>   alias = CKLF, <br>   gene_id = ENSG00000170558 (Ensembl ID), <br>   hgnc_id = HGNC:13723. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "proteinsFromGenes",
  "description": "Retrieve proteins from genes.<br>   Set verbose = true to retrieve full info on the proteins. <br>   Example: gene_name = ATF3, <br>   alias = CKLF, <br>   gene_id = ENSG00000170558 (Ensembl ID), <br>   hgnc_id = HGNC:13723. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
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
                "protein": {
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
                        "name": {
                          "type": "string",
                          "nullable": true
                        },
                        "uniprot_names": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "uniprot_full_names": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "uniprot_ids": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "dbxrefs": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "properties": {
                              "name": {
                                "type": "string"
                              },
                              "id": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "name",
                              "id"
                            ],
                            "additionalProperties": false
                          },
                          "nullable": true
                        },
                        "MANE_Select": {
                          "type": "boolean",
                          "nullable": true
                        },
                        "organism": {
                          "type": "string"
                        },
                        "source": {
                          "type": "string"
                        },
                        "source_url": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "_id",
                        "organism",
                        "source",
                        "source_url"
                      ],
                      "additionalProperties": false
                    }
                  ]
                }
              },
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
