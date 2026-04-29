# `GET /variants/genomic-elements`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts)

## Description

Retrieve genomic elements associated with a given variant.<br>   Example: variant_id = NC_000005.10:1779621:C:G, <br>   spdi = NC_000005.10:1779621:C:G,<br>   hgvs = NC_000005.10:g.1779622C>G, <br>   rsid = rs1735214522, <br>   ca_id = CA1522823495, <br>   region = chr5:1779619-1779629, <br>   biosample_term = EFO_0002067, <br>   biological_context = K562, <br>   method = BlueSTARR, <br>   files_fileset = IGVFFI1663LKVQ, <br>   The limit parameter controls the page size and can not exceed 300. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genomicElementsFromVariants",
  "description": "Retrieve genomic elements associated with a given variant.<br>   Example: variant_id = NC_000005.10:1779621:C:G, <br>   spdi = NC_000005.10:1779621:C:G,<br>   hgvs = NC_000005.10:g.1779622C>G, <br>   rsid = rs1735214522, <br>   ca_id = CA1522823495, <br>   region = chr5:1779619-1779629, <br>   biosample_term = EFO_0002067, <br>   biological_context = K562, <br>   method = BlueSTARR, <br>   files_fileset = IGVFFI1663LKVQ, <br>   The limit parameter controls the page size and can not exceed 300. <br>   Pagination is 0-based.",
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
    },
    {
      "name": "biosample_term",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "biological_context",
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
                "name": {
                  "type": "string"
                },
                "label": {
                  "type": "string"
                },
                "method": {
                  "type": "string"
                },
                "class": {
                  "type": "string",
                  "nullable": true
                },
                "log2FC": {
                  "type": "number",
                  "nullable": true
                },
                "nlog10pval": {
                  "type": "number",
                  "nullable": true
                },
                "beta": {
                  "type": "number",
                  "nullable": true
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                },
                "biological_context": {
                  "type": "string",
                  "nullable": true
                },
                "biosample_term": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string",
                  "nullable": true
                },
                "source_url": {
                  "type": "string",
                  "nullable": true
                },
                "genomic_element": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "name": {
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
                    },
                    "type": {
                      "type": "string"
                    },
                    "source_annotation": {
                      "type": "string",
                      "nullable": true
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
                    "name",
                    "chr",
                    "start",
                    "end",
                    "type",
                    "source",
                    "source_url"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                }
              },
              "required": [
                "variant",
                "name",
                "label",
                "method"
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
