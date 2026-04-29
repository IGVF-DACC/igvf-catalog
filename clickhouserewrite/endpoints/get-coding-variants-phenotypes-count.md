# `GET /coding-variants/phenotypes-count`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts)

## Description

Retrieve counts of coding variants associated with phenotypes.<br>     Example: gene_id = ENSG00000165841, <br>     files_fileset = IGVFFI6893ZOAA.

## OpenAPI excerpt

```json
{
  "operationId": "codingVariantsCountFromGene",
  "description": "Retrieve counts of coding variants associated with phenotypes.<br>     Example: gene_id = ENSG00000165841, <br>     files_fileset = IGVFFI6893ZOAA.",
  "parameters": [
    {
      "name": "gene_id",
      "in": "query",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "files_fileset",
      "in": "query",
      "required": false,
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
