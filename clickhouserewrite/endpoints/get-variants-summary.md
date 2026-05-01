# `GET /variants/summary`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts)

## Description

Retrieve genetic variants summary.<br>    Example: variant_id = NC_000020.11:3658947:A:G, <br>    spdi = NC_000020.11:3658947:A:G, <br>    hgvs = NC_000020.11:g.3658948A>G. <br>    ca_id = CA739473472

## OpenAPI excerpt

```json
{
  "operationId": "variantSummary",
  "description": "Retrieve genetic variants summary.<br>    Example: variant_id = NC_000020.11:3658947:A:G, <br>    spdi = NC_000020.11:3658947:A:G, <br>    hgvs = NC_000020.11:g.3658948A>G. <br>    ca_id = CA739473472",
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
    }
  ],
  "responses": {
    "200": {
      "description": "Successful response",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "summary": {
                "type": "object",
                "properties": {
                  "rsid": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "nullable": true
                  },
                  "varinfo": {
                    "type": "string",
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
              "allele_frequencies_gnomad": {},
              "cadd_scores": {
                "type": "object",
                "properties": {
                  "raw": {
                    "type": "number",
                    "nullable": true
                  },
                  "phread": {
                    "type": "number",
                    "nullable": true
                  }
                },
                "additionalProperties": false,
                "nullable": true
              },
              "nearest_genes": {
                "type": "object",
                "properties": {
                  "nearestCodingGene": {
                    "type": "object",
                    "properties": {
                      "gene_name": {
                        "type": "string",
                        "nullable": true
                      },
                      "id": {
                        "type": "string"
                      },
                      "start": {
                        "type": "number"
                      },
                      "end": {
                        "type": "number"
                      },
                      "distance": {
                        "type": "number"
                      }
                    },
                    "required": [
                      "id",
                      "start",
                      "end",
                      "distance"
                    ],
                    "additionalProperties": false
                  },
                  "nearestGene": {
                    "type": "object",
                    "properties": {
                      "gene_name": {
                        "type": "string",
                        "nullable": true
                      },
                      "id": {
                        "type": "string"
                      },
                      "start": {
                        "type": "number"
                      },
                      "end": {
                        "type": "number"
                      },
                      "distance": {
                        "type": "number"
                      }
                    },
                    "required": [
                      "id",
                      "start",
                      "end",
                      "distance"
                    ],
                    "additionalProperties": false
                  }
                },
                "required": [
                  "nearestCodingGene",
                  "nearestGene"
                ],
                "additionalProperties": false
              }
            },
            "required": [
              "summary",
              "nearest_genes"
            ],
            "additionalProperties": false
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

Endpoint code is unchanged in `variants.ts`; the previous breakage was its dependency on the still-AQL `nearestGeneSearch` in `genes.ts`. That dependency is now ClickHouse-native — see [`get-genes.md`](get-genes.md) and [`routers/genes.md`](../routers/genes.md). All four input forms (`variant_id`, `rsid`, `spdi`, `region`) verified live.
