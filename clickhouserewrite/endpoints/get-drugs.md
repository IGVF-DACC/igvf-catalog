# `GET /drugs`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/drugs.ts`](../../src/routers/datatypeRouters/nodes/drugs.ts)

## Description

Retrieve drugs (chemicals). <br>   Example: drug_id = PA448497 (chemical ids from pharmGKB), <br>   name = aspirin.<br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "drugs",
  "description": "Retrieve drugs (chemicals). <br>   Example: drug_id = PA448497 (chemical ids from pharmGKB), <br>   name = aspirin.<br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "drug_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "name",
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
            "anyOf": [
              {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "name": {
                      "type": "string"
                    },
                    "drug_ontology_terms": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
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
                    "source",
                    "source_url"
                  ],
                  "additionalProperties": false
                }
              },
              {
                "type": "object",
                "properties": {
                  "_id": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  },
                  "drug_ontology_terms": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                  "source",
                  "source_url"
                ],
                "additionalProperties": false
              }
            ]
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
