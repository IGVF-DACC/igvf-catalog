# `GET /coding-variants/variants`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_coding_variants.ts`](../../src/routers/datatypeRouters/edges/variants_coding_variants.ts)

## Description

Retrieve variants associated with a coding variant.<br>     Example: coding_variant_name = OR4F5_ENST00000641515_p.Gly30Ser_c.88G-A, <br>     hgvsp = p.Gly30Ser, <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromCodingVariants",
  "description": "Retrieve variants associated with a coding variant.<br>     Example: coding_variant_name = OR4F5_ENST00000641515_p.Gly30Ser_c.88G-A, <br>     hgvsp = p.Gly30Ser, <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.",
  "parameters": [
    {
      "name": "coding_variant_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "hgvsp",
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
                "alt",
                "_id"
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
