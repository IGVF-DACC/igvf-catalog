# `GET /variants/region-summary`

**Status:** ❓ Not in router files

**Router file:** _(not found in router files)_

## Description

Retrieve a summary count of all methods reporting variants in a given region.<br>     Example: region = chr1:1157520-1158520 (maximum length: 10kb).

## OpenAPI excerpt

```json
{
  "operationId": "variantsRegionSummary",
  "description": "Retrieve a summary count of all methods reporting variants in a given region.<br>     Example: region = chr1:1157520-1158520 (maximum length: 10kb).",
  "parameters": [
    {
      "name": "region",
      "in": "query",
      "required": true,
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
              "variant_count": {
                "type": "number"
              },
              "by_method": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "method": {
                      "type": "string"
                    },
                    "count": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "method",
                    "count"
                  ],
                  "additionalProperties": false
                }
              }
            },
            "required": [
              "variant_count",
              "by_method"
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
