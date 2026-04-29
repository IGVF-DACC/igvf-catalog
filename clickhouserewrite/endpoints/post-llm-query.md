# `POST /llm-query`

**Status:** ℹ︎ No DB call

**Router file:** [`src/routers/datatypeRouters/nodes/llm_query.ts`](../../src/routers/datatypeRouters/nodes/llm_query.ts)

## Description

Ask a question that interests you. This API is password protected.<br>   Set verbose = true to retrieve AQL and AQL results.<br>   Example: query = Tell me about the gene SAMD11.

## OpenAPI excerpt

```json
{
  "operationId": "llmQuery",
  "description": "Ask a question that interests you. This API is password protected.<br>   Set verbose = true to retrieve AQL and AQL results.<br>   Example: query = Tell me about the gene SAMD11.",
  "requestBody": {
    "required": true,
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "maxLength": 5000
            },
            "password": {
              "type": "string"
            },
            "verbose": {
              "type": "string",
              "enum": [
                "true",
                "false"
              ],
              "default": "false"
            }
          },
          "required": [
            "query",
            "password"
          ],
          "additionalProperties": false
        }
      }
    }
  },
  "parameters": [],
  "responses": {
    "200": {
      "description": "Successful response",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string"
              },
              "aql": {
                "type": "string",
                "maxLength": 5000
              },
              "aql_result": {
                "type": "array",
                "maxItems": 5
              },
              "answer": {
                "type": "string"
              }
            },
            "required": [
              "query",
              "answer"
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
