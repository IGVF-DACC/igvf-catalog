# `GET /genes/coding-variants/scores`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/edges/genes_coding_variants.ts`](../../src/routers/datatypeRouters/edges/genes_coding_variants.ts)

## Description

Retrieve scores and predictions of associated coding variants for one specific gene.<br>   Example: gene_id = ENSG00000196584, gene_name = XRCC2, alias = FANCU, hgnc_id = HGNC:12829, method = MutPred2, files_fileset = IGVFFI6893ZOAA. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "codingVariantsFromGenes",
  "description": "Retrieve scores and predictions of associated coding variants for one specific gene.<br>   Example: gene_id = ENSG00000196584, gene_name = XRCC2, alias = FANCU, hgnc_id = HGNC:12829, method = MutPred2, files_fileset = IGVFFI6893ZOAA. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "ESM-1v",
          "MutPred2",
          "SGE",
          "VAMP-seq"
        ]
      }
    },
    {
      "name": "files_fileset",
      "in": "query",
      "required": false,
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
                "protein_change": {
                  "type": "object",
                  "properties": {
                    "protein_id": {
                      "type": "string",
                      "nullable": true
                    },
                    "protein_name": {
                      "type": "string",
                      "nullable": true
                    },
                    "transcript_id": {
                      "type": "string",
                      "nullable": true
                    },
                    "hgvsp": {
                      "type": "string",
                      "nullable": true
                    },
                    "aapos": {
                      "type": "number",
                      "nullable": true
                    },
                    "ref": {
                      "type": "string",
                      "nullable": true
                    },
                    "alt": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "additionalProperties": false
                },
                "variants": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "variant": {
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
                      },
                      "scores": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "method": {
                              "type": "string"
                            },
                            "score": {
                              "type": "number",
                              "nullable": true
                            },
                            "source_url": {
                              "type": "string",
                              "nullable": true
                            },
                            "files_filesets": {
                              "type": "string",
                              "nullable": true
                            }
                          },
                          "required": [
                            "method"
                          ],
                          "additionalProperties": false
                        }
                      }
                    },
                    "required": [
                      "variant",
                      "scores"
                    ],
                    "additionalProperties": false
                  },
                  "nullable": true
                }
              },
              "required": [
                "protein_change"
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
