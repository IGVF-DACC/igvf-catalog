# `GET /ontology-terms/{ontology_term_id}/children`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts`](../../src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts)

## Description

Retrieve all child nodes of an ontology term.<br>   Example: ontology_term_id = CHEBI_20857. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "ontologyTermChildren",
  "description": "Retrieve all child nodes of an ontology term.<br>   Example: ontology_term_id = CHEBI_20857. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "ontology_term_id",
      "in": "path",
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
              "anyOf": [
                {
                  "not": {}
                },
                {
                  "type": "object",
                  "properties": {
                    "term": {
                      "type": "object",
                      "properties": {
                        "uri": {
                          "type": "string"
                        },
                        "term_id": {
                          "type": "string"
                        },
                        "name": {
                          "type": "string"
                        },
                        "synonyms": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "description": {
                          "type": "string",
                          "nullable": true
                        },
                        "source": {
                          "type": "string"
                        },
                        "subontology": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_url": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "uri",
                        "term_id",
                        "name"
                      ],
                      "additionalProperties": false
                    },
                    "relationship_type": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "term",
                    "relationship_type"
                  ],
                  "additionalProperties": false
                }
              ]
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
