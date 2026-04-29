# `GET /variants/variant-ld/summary`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_variants.ts`](../../src/routers/datatypeRouters/edges/variants_variants.ts)

## Description

Retrieve a summary of genetic variants in linkage disequilibrium (LD).<br>     Example: variant_id = NC_000001.11:954257:G:C, hgvs = NC_000011.10:g.9090011A>G, spdi = NC_000011.10:9090010:A:G, ca_id = CA10655063. The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromVariantIDSummary",
  "description": "Retrieve a summary of genetic variants in linkage disequilibrium (LD).<br>     Example: variant_id = NC_000001.11:954257:G:C, hgvs = NC_000011.10:g.9090011A>G, spdi = NC_000011.10:9090010:A:G, ca_id = CA10655063. The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.",
  "parameters": [
    {
      "name": "spdi",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "hgvs",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "ca_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "variant_id",
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
                "ancestry": {
                  "type": "string"
                },
                "d_prime": {
                  "type": "number",
                  "nullable": true
                },
                "r2": {
                  "type": "number",
                  "nullable": true
                },
                "sequence variant": {
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
                          "type": "string",
                          "nullable": true
                        },
                        "hgvs": {
                          "type": "string",
                          "nullable": true
                        },
                        "ca_id": {
                          "type": "string",
                          "nullable": true
                        },
                        "_id": {
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
                  ]
                },
                "predictions": {
                  "type": "object",
                  "properties": {
                    "qtls": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "type": {
                            "type": "string"
                          },
                          "cell_types": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "name": {
                                  "type": "string",
                                  "nullable": true
                                },
                                "count": {
                                  "type": "number"
                                }
                              },
                              "required": [
                                "name",
                                "count"
                              ],
                              "additionalProperties": false
                            }
                          },
                          "genes": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "name": {
                                  "type": "string"
                                },
                                "count": {
                                  "type": "number"
                                }
                              },
                              "required": [
                                "name",
                                "count"
                              ],
                              "additionalProperties": false
                            }
                          }
                        },
                        "required": [
                          "type",
                          "cell_types",
                          "genes"
                        ],
                        "additionalProperties": false
                      },
                      "nullable": true
                    },
                    "tf_binding": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "motif": {
                            "type": "string"
                          },
                          "count": {
                            "type": "number"
                          },
                          "cell_types": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "cell_type": {
                                  "type": "string",
                                  "nullable": true
                                },
                                "count": {
                                  "type": "number"
                                }
                              },
                              "required": [
                                "cell_type",
                                "count"
                              ],
                              "additionalProperties": false
                            }
                          }
                        },
                        "required": [
                          "motif",
                          "count",
                          "cell_types"
                        ],
                        "additionalProperties": false
                      },
                      "nullable": true
                    }
                  },
                  "additionalProperties": false
                }
              },
              "required": [
                "ancestry",
                "sequence variant",
                "predictions"
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
