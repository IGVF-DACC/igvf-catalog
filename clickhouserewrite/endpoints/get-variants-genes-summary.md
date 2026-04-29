# `GET /variants/genes/summary`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts)

## Description

Retrieve a summary of associated genes from GTEx eQTLs & splice QTLs by internal variant ids.<br>     Example: variant_id = NC_000001.11:920568:G:A, spdi = NC_000001.11:920568:G:A, hgvs = NC_000001.11:g.920569G>A, ca_id = CA10655131, files_fileset = IGVFFI9602ILPC.

## OpenAPI excerpt

```json
{
  "operationId": "qtlSummaryEndpoint",
  "description": "Retrieve a summary of associated genes from GTEx eQTLs & splice QTLs by internal variant ids.<br>     Example: variant_id = NC_000001.11:920568:G:A, spdi = NC_000001.11:920568:G:A, hgvs = NC_000001.11:g.920569G>A, ca_id = CA10655131, files_fileset = IGVFFI9602ILPC. ",
  "parameters": [
    {
      "name": "spdi",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "hgvs",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "ca_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "variant_id",
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
          "Mus musculus",
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
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
                "qtl_type": {
                  "type": "string"
                },
                "log10pvalue": {
                  "type": "number",
                  "nullable": true
                },
                "chr": {
                  "type": "string"
                },
                "biological_context": {
                  "type": "string",
                  "nullable": true
                },
                "effect_size": {
                  "type": "number",
                  "nullable": true
                },
                "gene": {
                  "type": "object",
                  "properties": {
                    "gene_name": {
                      "type": "string"
                    },
                    "gene_id": {
                      "type": "string"
                    },
                    "gene_start": {
                      "type": "number"
                    },
                    "gene_end": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "gene_name",
                    "gene_id",
                    "gene_start",
                    "gene_end"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                },
                "name": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "qtl_type",
                "chr"
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
