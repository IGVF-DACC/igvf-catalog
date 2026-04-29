# `GET /variants/genomic-elements/cell-gene-predictions`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts)

## Description

Retrieve predicted associated genes and cell types for a given variant. <br>   Example: variant_id = NC_000012.12:69248967:C:T, spdi = NC_000012.12:69248967:C:T, <br>   hgvs = NC_000012.12:g.69248968C>T, rsid = rs544450198, ca_id = CA10655063, region = chr1:1157520-1158189 (maximum length: 10kb).

## OpenAPI excerpt

```json
{
  "operationId": "genomicElementsPredictionsFromVariant",
  "description": "Retrieve predicted associated genes and cell types for a given variant. <br>   Example: variant_id = NC_000012.12:69248967:C:T, spdi = NC_000012.12:69248967:C:T, <br>   hgvs = NC_000012.12:g.69248968C>T, rsid = rs544450198, ca_id = CA10655063, region = chr1:1157520-1158189 (maximum length: 10kb).",
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
      "name": "rsid",
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
      "name": "region",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
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
              "sequence variant": {
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
                  }
                },
                "required": [
                  "_id",
                  "chr",
                  "pos",
                  "rsid",
                  "ref",
                  "alt",
                  "spdi",
                  "hgvs"
                ],
                "additionalProperties": false
              },
              "predictions": {
                "type": "object",
                "properties": {
                  "cell_types": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "genes": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "gene_name": {
                          "type": "string",
                          "nullable": true
                        },
                        "id": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "gene_name",
                        "id"
                      ],
                      "additionalProperties": false
                    }
                  }
                },
                "required": [
                  "cell_types",
                  "genes"
                ],
                "additionalProperties": false
              }
            },
            "required": [
              "sequence variant",
              "predictions"
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

_(none yet)_
