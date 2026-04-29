# `GET /diseases/variants`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_diseases.ts`](../../src/routers/datatypeRouters/edges/variants_diseases.ts)

## Description

Retrieve variants and genes associated with the query disease from ClinGen. <br>   Example: disease_id = MONDO_0009861, <br>   disease_name = phenylketonuria, <br>   pmid = 2574002. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromDiseases",
  "description": "Retrieve variants and genes associated with the query disease from ClinGen. <br>   Example: disease_id = MONDO_0009861, <br>   disease_name = phenylketonuria, <br>   pmid = 2574002. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
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
      "name": "assertion",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Benign",
          "Likely Benign",
          "Likely Pathogenic",
          "Pathogenic",
          "Uncertain Significance"
        ]
      }
    },
    {
      "name": "pmid",
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
                "sequence_variant": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
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
                        },
                        "ca_id": {
                          "type": "string",
                          "nullable": true
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
                "gene_id": {
                  "type": "string"
                },
                "gene_name": {
                  "type": "string"
                },
                "assertion": {
                  "type": "string"
                },
                "pmids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
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
