# `GET /ontology-terms`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/ontologies.ts`](../../src/routers/datatypeRouters/nodes/ontologies.ts)

## Description

Retrieve ontology terms.<br>   Example: term_id = Orphanet_101435, <br>   name = Rare genetic eye disease, <br>   synonyms = WTC11, <br>   source = EFO, <br>   subontology = molecular_function. <br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "ontologyTerm",
  "description": "Retrieve ontology terms.<br>   Example: term_id = Orphanet_101435, <br>   name = Rare genetic eye disease, <br>   synonyms = WTC11, <br>   source = EFO, <br>   subontology = molecular_function. <br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "term_id",
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
      "name": "synonyms",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "description",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "source",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "BAO",
          "CHEBI",
          "CL",
          "CLO",
          "Cellosaurus",
          "EFO",
          "ENCODE",
          "GO",
          "HPO",
          "IGVF",
          "MONDO",
          "NCIT",
          "OBA",
          "ORPHANET",
          "Oncotree",
          "UBERON",
          "VARIO"
        ]
      }
    },
    {
      "name": "subontology",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "biological_process",
          "cellular_component",
          "molecular_function"
        ]
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
