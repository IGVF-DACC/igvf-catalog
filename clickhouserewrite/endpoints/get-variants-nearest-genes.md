# `GET /variants/nearest-genes`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts)

## Description

Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. <br>   Example: region = chr1:11868-14409 or region = chr1:1157520-1158189 (maximum length: 10kb).

## OpenAPI excerpt

```json
{
  "operationId": "nearestGenes",
  "description": "Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. <br>   Example: region = chr1:11868-14409 or region = chr1:1157520-1158189 (maximum length: 10kb).",
  "parameters": [
    {
      "name": "region",
      "in": "query",
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
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "_id": {
                  "type": "string"
                },
                "chr": {
                  "type": "string"
                },
                "start": {
                  "type": "number",
                  "nullable": true
                },
                "end": {
                  "type": "number",
                  "nullable": true
                },
                "gene_type": {
                  "type": "string",
                  "nullable": true
                },
                "name": {
                  "type": "string"
                },
                "strand": {
                  "type": "string",
                  "nullable": true
                },
                "hgnc": {
                  "type": "string",
                  "nullable": true
                },
                "entrez": {
                  "type": "string",
                  "nullable": true
                },
                "collections": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "study_sets": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "version": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "synonyms": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "chr",
                "start",
                "end",
                "gene_type",
                "name",
                "source",
                "version",
                "source_url"
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
