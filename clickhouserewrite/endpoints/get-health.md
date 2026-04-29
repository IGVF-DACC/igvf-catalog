# `GET /health`

**Status:** ℹ︎ No DB call

**Router file:** [`src/routers/datatypeRouters/nodes/health.ts`](../../src/routers/datatypeRouters/nodes/health.ts)

## Description

Health check endpoint for the API service

## OpenAPI excerpt

```json
{
  "operationId": "health",
  "description": "Health check endpoint for the API service",
  "parameters": [],
  "responses": {
    "200": {
      "description": "Successful response",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "status": {
                "type": "string"
              }
            },
            "required": [
              "status"
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
