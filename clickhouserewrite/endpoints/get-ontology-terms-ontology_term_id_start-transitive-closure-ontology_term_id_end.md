# `GET /ontology-terms/{ontology_term_id_start}/transitive-closure/{ontology_term_id_end}`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts`](../../src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts)

## Description

Retrieve all paths between two ontology terms (i.e. transitive closure).<br>   Example: ontology_term_id_start = UBERON_0003663, <br>   ontology_term_id_end = UBERON_0014892

## OpenAPI excerpt

```json
{
  "operationId": "ontologyTermTransitiveClosure",
  "description": "Retrieve all paths between two ontology terms (i.e. transitive closure).<br>   Example: ontology_term_id_start = UBERON_0003663, <br>   ontology_term_id_end = UBERON_0014892",
  "parameters": [
    {
      "name": "ontology_term_id_start",
      "in": "path",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "ontology_term_id_end",
      "in": "path",
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
              "vertices": {
                "type": "object",
                "additionalProperties": {
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
                      }
                    },
                    "description": {
                      "type": "string"
                    },
                    "source": {
                      "type": "string"
                    },
                    "subontology": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "uri",
                    "term_id",
                    "name",
                    "synonyms",
                    "description",
                    "source"
                  ],
                  "additionalProperties": false
                }
              },
              "paths": {
                "type": "array",
                "items": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "from": {
                        "type": "string"
                      },
                      "to": {
                        "type": "string"
                      },
                      "name": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "from",
                      "to",
                      "name"
                    ],
                    "additionalProperties": false
                  }
                }
              }
            },
            "required": [
              "vertices",
              "paths"
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
