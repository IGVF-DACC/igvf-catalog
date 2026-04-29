# `GET /genes/coding-variants/all-scores`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/edges/genes_coding_variants.ts`](../../src/routers/datatypeRouters/edges/genes_coding_variants.ts)

## Description

Retrieve scores and predictions of associated coding variants for one specific gene.<br>   Example: gene_id = ENSG00000196584, gene_name = XRCC2, alias = FANCU, hgnc_id = HGNC:12829, method = MutPred2, files_fileset = IGVFFI6893ZOAA. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "allCodingVariantsFromGenes",
  "description": "Retrieve scores and predictions of associated coding variants for one specific gene.<br>   Example: gene_id = ENSG00000196584, gene_name = XRCC2, alias = FANCU, hgnc_id = HGNC:12829, method = MutPred2, files_fileset = IGVFFI6893ZOAA. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "dataset",
      "in": "query",
      "required": true,
      "schema": {
        "type": "string",
        "enum": [
          "ESM-1v",
          "MutPred2",
          "SGE",
          "VAMP-seq"
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
                  "type": "number"
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
