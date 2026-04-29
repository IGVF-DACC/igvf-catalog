# `GET /go-terms/gene-products`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/go_terms_annotations.ts`](../../src/routers/datatypeRouters/edges/go_terms_annotations.ts)

## Description

Retrieve annotations associated with a GO term. <br>   Example: go_term_id = GO_1990590. <br>   name = 'has component' or 'contains' or 'is a function of' <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "annotationsFromGoTerms",
  "description": "Retrieve annotations associated with a GO term. <br>   Example: go_term_id = GO_1990590. <br>   name = 'has component' or 'contains' or 'is a function of' <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "go_term_id",
      "in": "query",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "contains",
          "has component",
          "is a function of"
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
              "anyOf": [
                {
                  "not": {}
                },
                {
                  "type": "object",
                  "properties": {
                    "gene_product_id": {
                      "type": "string"
                    },
                    "gene_product_name": {
                      "type": "string",
                      "nullable": true
                    },
                    "go_term_name": {
                      "type": "string"
                    },
                    "source": {
                      "type": "string"
                    },
                    "gene_product_type": {
                      "type": "string"
                    },
                    "gene_product_symbol": {
                      "type": "string"
                    },
                    "qualifier": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "organism": {
                      "type": "string"
                    },
                    "evidence": {
                      "type": "string"
                    },
                    "go_id": {
                      "type": "string"
                    },
                    "name": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "gene_product_id",
                    "go_term_name",
                    "source",
                    "gene_product_type",
                    "gene_product_symbol",
                    "qualifier",
                    "organism",
                    "evidence",
                    "go_id",
                    "name"
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
