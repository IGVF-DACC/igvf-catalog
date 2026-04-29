# `GET /variants/gnomad-alleles`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts)

## Description

Retrieve GNOMAD alleles for variants in a given region.<br>    Example: region = chr1:1157520-1158520 (maximum length: 10kb).<br>    Region limit: 1kb pairs.

## OpenAPI excerpt

```json
{
  "operationId": "variantsAlleles",
  "description": "Retrieve GNOMAD alleles for variants in a given region.<br>    Example: region = chr1:1157520-1158520 (maximum length: 10kb).<br>    Region limit: 1kb pairs.",
  "parameters": [
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
            "type": "array",
            "items": {
              "type": "array",
              "items": {
                "anyOf": [
                  {
                    "not": {}
                  },
                  {
                    "anyOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "number"
                      }
                    ],
                    "nullable": true
                  }
                ]
              }
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
