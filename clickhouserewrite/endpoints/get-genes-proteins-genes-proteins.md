# `GET /genes-proteins/genes-proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_proteins_variants.ts`](../../src/routers/datatypeRouters/edges/genes_proteins_variants.ts)

## Description

Retrieve genes or proteins associated with either genes or proteins that match a query. <br>   Example: query = ATF1.<br>   The limit parameter controls the page size of related items and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesProteinsGenesProteins",
  "description": "Retrieve genes or proteins associated with either genes or proteins that match a query. <br>   Example: query = ATF1.<br>   The limit parameter controls the page size of related items and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "query",
      "in": "query",
      "required": true,
      "schema": {
        "type": "string"
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
                "protein": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "name": {
                      "type": "string"
                    },
                    "uniprot_names": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "files_filesets": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "_id",
                    "name",
                    "uniprot_names"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                },
                "gene": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "chr": {
                      "type": "string"
                    },
                    "gene_id": {
                      "type": "string"
                    },
                    "hgnc": {
                      "type": "string",
                      "nullable": true
                    },
                    "name": {
                      "type": "string"
                    },
                    "organism": {
                      "type": "string"
                    },
                    "files_filesets": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "_id",
                    "chr",
                    "gene_id",
                    "name",
                    "organism"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                },
                "related": {
                  "type": "array",
                  "items": {
                    "anyOf": [
                      {
                        "type": "object",
                        "properties": {
                          "_id": {
                            "type": "string"
                          },
                          "name": {
                            "type": "string"
                          },
                          "uniprot_names": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "files_filesets": {
                            "type": "string",
                            "nullable": true
                          }
                        },
                        "required": [
                          "_id",
                          "name",
                          "uniprot_names"
                        ],
                        "additionalProperties": false
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
                          "gene_id": {
                            "type": "string"
                          },
                          "hgnc": {
                            "type": "string",
                            "nullable": true
                          },
                          "name": {
                            "type": "string"
                          },
                          "organism": {
                            "type": "string"
                          },
                          "files_filesets": {
                            "type": "string",
                            "nullable": true
                          }
                        },
                        "required": [
                          "_id",
                          "chr",
                          "gene_id",
                          "name",
                          "organism"
                        ],
                        "additionalProperties": false
                      }
                    ]
                  },
                  "nullable": true
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
