# `GET /variants/phenotypes/score-summary`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts)

## Description

DEPRECATED. Please use coding-variants/phenotypes/summary.<br>     Retrieve scores of variants associated with phenotypes. Via coding variants edges.<br>     Example: variant_id = NC_000018.10:31546002:CA:GT, <br>     coding_variant_name = DSG2_ENST00000261590_p.Gln873Val_c.2617_2618delinsGT, <br>     files_fileset = IGVFFI6893ZOAA.

## OpenAPI excerpt

```json
{
  "operationId": "deprecatedCodingVariantsSummary",
  "description": "DEPRECATED. Please use coding-variants/phenotypes/summary.<br>     Retrieve scores of variants associated with phenotypes. Via coding variants edges.<br>     Example: variant_id = NC_000018.10:31546002:CA:GT, <br>     coding_variant_name = DSG2_ENST00000261590_p.Gln873Val_c.2617_2618delinsGT, <br>     files_fileset = IGVFFI6893ZOAA.",
  "parameters": [
    {
      "name": "variant_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "coding_variant_id",
      "in": "query",
      "required": false,
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
                "variant_id": {
                  "type": "string",
                  "nullable": true
                },
                "hgvsp": {
                  "type": "string",
                  "nullable": true
                },
                "gene_name": {
                  "type": "string",
                  "nullable": true
                },
                "transcript_id": {
                  "type": "string",
                  "nullable": true
                },
                "dataType": {
                  "type": "string"
                },
                "score": {
                  "type": "number",
                  "nullable": true
                },
                "portalLink": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "dataType",
                "score",
                "portalLink"
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
