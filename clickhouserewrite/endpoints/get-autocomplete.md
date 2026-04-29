# `GET /autocomplete`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/autocomplete.ts`](../../src/routers/datatypeRouters/autocomplete.ts)

## Description

Autocomplete names for genes and proteins based on prefix search.<br>   Example: term = TP53, <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "autocomplete",
  "description": "Autocomplete names for genes and proteins based on prefix search.<br>   Example: term = TP53, <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "term",
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
                "term": {
                  "type": "string"
                },
                "type": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                },
                "uri": {
                  "type": "string"
                }
              },
              "required": [
                "term",
                "type",
                "name",
                "uri"
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
