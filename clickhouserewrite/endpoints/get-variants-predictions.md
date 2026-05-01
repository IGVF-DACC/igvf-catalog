# `GET /variants/predictions`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts)

## Description

Retrieve element gene predictions associated with a given variant.<br>   Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br>   spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941, ca_id = CA10655131, files_fileset = ENCFF705MLV.<br>   The limit parameter controls the page size and can not exceed 300. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "predictionsFromVariants",
  "description": "Retrieve element gene predictions associated with a given variant.<br>   Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br>   spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941, ca_id = CA10655131, files_fileset = ENCFF705MLV.<br>   The limit parameter controls the page size and can not exceed 300. <br>   Pagination is 0-based.",
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
      "name": "files_fileset",
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
          "caQTL"
        ]
      }
    },
    {
      "name": "limit",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number"
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
                "distance_gene_variant": {
                  "type": "number"
                },
                "element_chr": {
                  "type": "string"
                },
                "element_start": {
                  "type": "number"
                },
                "element_end": {
                  "type": "number"
                },
                "element_type": {
                  "type": "string"
                },
                "id": {
                  "type": "string"
                },
                "cell_type": {
                  "type": "string"
                },
                "target_gene": {
                  "type": "object",
                  "properties": {
                    "gene_name": {
                      "type": "string"
                    },
                    "id": {
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
                    }
                  },
                  "required": [
                    "gene_name",
                    "id",
                    "chr",
                    "start",
                    "end"
                  ],
                  "additionalProperties": false
                },
                "score": {
                  "type": "number"
                },
                "model": {
                  "type": "string"
                },
                "dataset": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "distance_gene_variant",
                "element_chr",
                "element_start",
                "element_end",
                "element_type",
                "id",
                "cell_type",
                "target_gene",
                "score",
                "model",
                "dataset",
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
