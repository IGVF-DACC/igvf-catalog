# `GET /variants/genes-proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_proteins_variants.ts`](../../src/routers/datatypeRouters/edges/genes_proteins_variants.ts)

## Description

Retrieve genes and proteins associated with a variant matched by ID. <br>   Example: variant_id = NC_000001.11:630556:T:C.<br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesProteinsFromVariants",
  "description": "Retrieve genes and proteins associated with a variant matched by ID. <br>   Example: variant_id = NC_000001.11:630556:T:C.<br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "variant_id",
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
                "sequence_variant": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "chr": {
                      "type": "string"
                    },
                    "pos": {
                      "type": "number"
                    },
                    "rsid": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "nullable": true
                    },
                    "ref": {
                      "type": "string"
                    },
                    "alt": {
                      "type": "string"
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
                    "_id",
                    "chr",
                    "pos",
                    "ref",
                    "alt",
                    "spdi",
                    "hgvs"
                  ],
                  "additionalProperties": false
                },
                "related": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gene": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "not": {}
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
                              }
                            ]
                          },
                          {
                            "anyOf": [
                              {
                                "not": {}
                              },
                              {
                                "type": "string",
                                "nullable": true
                              }
                            ]
                          }
                        ]
                      },
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
                      "sources": {
                        "anyOf": [
                          {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "label": {
                                  "type": "string"
                                },
                                "source": {
                                  "type": "string"
                                },
                                "log10pvalue": {
                                  "type": "number",
                                  "nullable": true
                                },
                                "biological_context": {
                                  "type": "string"
                                },
                                "name": {
                                  "type": "string"
                                }
                              },
                              "required": [
                                "label",
                                "source",
                                "biological_context",
                                "name"
                              ],
                              "additionalProperties": false
                            }
                          },
                          {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "motif": {
                                  "type": "string",
                                  "nullable": true
                                },
                                "source": {
                                  "type": "string"
                                },
                                "name": {
                                  "type": "string"
                                }
                              },
                              "required": [
                                "motif",
                                "source",
                                "name"
                              ],
                              "additionalProperties": false
                            }
                          }
                        ]
                      }
                    },
                    "required": [
                      "sources"
                    ],
                    "additionalProperties": false
                  }
                }
              },
              "required": [
                "sequence_variant",
                "related"
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
