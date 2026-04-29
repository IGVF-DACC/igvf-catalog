# `GET /pathways`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/pathways.ts`](../../src/routers/datatypeRouters/nodes/pathways.ts)

## Description

Retrieve pathways from Reactome.<br>   Example: id = R-HSA-164843, <br>   name = 2-LTR circle formation, <br>   is_in_disease = true. <br>   name_aliases = 2-LTR circle formation, <br>   is_top_level_pathway = true. <br>   disease_ontology_terms = DOID_526, <br>   go_biological_process = GO_0006015. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "pathways",
  "description": "Retrieve pathways from Reactome.<br>   Example: id = R-HSA-164843, <br>   name = 2-LTR circle formation, <br>   is_in_disease = true. <br>   name_aliases = 2-LTR circle formation, <br>   is_top_level_pathway = true. <br>   disease_ontology_terms = DOID_526, <br>   go_biological_process = GO_0006015. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "id",
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
      "name": "is_in_disease",
      "in": "query",
      "required": false,
      "schema": {
        "type": "boolean"
      }
    },
    {
      "name": "name_aliases",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "is_top_level_pathway",
      "in": "query",
      "required": false,
      "schema": {
        "type": "boolean"
      }
    },
    {
      "name": "disease_ontology_terms",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "go_biological_process",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "organism",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
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
                "_id": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                },
                "organism": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "id_version": {
                  "type": "string"
                },
                "is_in_disease": {
                  "type": "boolean"
                },
                "name_aliases": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "is_top_level_pathway": {
                  "type": "boolean"
                },
                "disease_ontology_terms": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "go_biological_process": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "name",
                "organism",
                "source",
                "source_url",
                "id_version",
                "is_in_disease",
                "name_aliases",
                "is_top_level_pathway",
                "disease_ontology_terms",
                "go_biological_process"
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
