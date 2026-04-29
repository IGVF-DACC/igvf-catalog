# `GET /diseases/genes`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/diseases_genes.ts`](../../src/routers/datatypeRouters/edges/diseases_genes.ts)

## Description

Retrieve disease-gene pairs from Orphanet by diseases.<br>     Set verbose = true to retrieve full info on the genes and diseases. <br>     Example: disease_name = fibrosis, <br>     disease_id = Orphanet_586, <br>     source = Orphanet. <br>     Either disease_name or disease_id are required. <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesFromDiseases",
  "description": "Retrieve disease-gene pairs from Orphanet by diseases.<br>     Set verbose = true to retrieve full info on the genes and diseases. <br>     Example: disease_name = fibrosis, <br>     disease_id = Orphanet_586, <br>     source = Orphanet. <br>     Either disease_name or disease_id are required. <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.",
  "parameters": [
    {
      "name": "disease_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "disease_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "source",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Orphanet"
        ],
        "default": "Orphanet"
      }
    },
    {
      "name": "organism",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
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
                "pmid": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "term_name": {
                  "type": "string"
                },
                "gene_symbol": {
                  "type": "string"
                },
                "association_type": {
                  "type": "string"
                },
                "association_status": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
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
                "disease": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "object",
                      "properties": {
                        "uri": {
                          "type": "string"
                        },
                        "term_id": {
                          "type": "string"
                        },
                        "name": {
                          "type": "string"
                        },
                        "synonyms": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "description": {
                          "type": "string",
                          "nullable": true
                        },
                        "source": {
                          "type": "string"
                        },
                        "subontology": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_url": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "uri",
                        "term_id",
                        "name"
                      ],
                      "additionalProperties": false
                    }
                  ]
                },
                "inheritance_mode": {
                  "type": "string"
                },
                "variants": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "chr": {
                        "type": "string"
                      },
                      "pos": {
                        "type": "number"
                      },
                      "ref": {
                        "type": "string"
                      },
                      "alt": {
                        "type": "string"
                      },
                      "rsid": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "nullable": true
                      },
                      "spdi": {
                        "type": "string"
                      },
                      "hgvs": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "chr",
                      "pos",
                      "ref",
                      "alt"
                    ],
                    "additionalProperties": false
                  }
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
