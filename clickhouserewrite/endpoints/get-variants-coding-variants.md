# `GET /variants/coding-variants`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_coding_variants.ts`](../../src/routers/datatypeRouters/edges/variants_coding_variants.ts)

## Description

Retrieve coding variants from dbSNFP associated with a variant.<br>     Example: variant_id = NC_000001.11:65564:A:T, <br>     spdi = NC_000001.11:65564:A:T, <br>     hgvs = NC_000001.11:g.65565A>T, <br>     ca_id = CA337806511, <br>     The limit parameter controls the page size and can not exceed 500.

## OpenAPI excerpt

```json
{
  "operationId": "codingVariantsFromVariants",
  "description": "Retrieve coding variants from dbSNFP associated with a variant.<br>     Example: variant_id = NC_000001.11:65564:A:T, <br>     spdi = NC_000001.11:65564:A:T, <br>     hgvs = NC_000001.11:g.65565A>T, <br>     ca_id = CA337806511, <br>     The limit parameter controls the page size and can not exceed 500.",
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
                  "type": "string",
                  "nullable": true
                },
                "ref": {
                  "type": "string",
                  "nullable": true
                },
                "alt": {
                  "type": "string",
                  "nullable": true
                },
                "protein_name": {
                  "type": "string",
                  "nullable": true
                },
                "protein_id": {
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
                "aapos": {
                  "type": "number",
                  "nullable": true
                },
                "hgvsp": {
                  "type": "string",
                  "nullable": true
                },
                "hgvsc": {
                  "type": "string",
                  "nullable": true
                },
                "refcodon": {
                  "type": "string",
                  "nullable": true
                },
                "codonpos": {
                  "type": "number",
                  "nullable": true
                },
                "SIFT_score": {
                  "type": "number",
                  "nullable": true
                },
                "SIFT4G_score": {
                  "type": "number",
                  "nullable": true
                },
                "Polyphen2_HDIV_score": {
                  "type": "number",
                  "nullable": true
                },
                "Polyphen2_HVAR_score": {
                  "type": "number",
                  "nullable": true
                },
                "VEST4_score": {
                  "type": "number",
                  "nullable": true
                },
                "Mcap_score": {
                  "type": "number",
                  "nullable": true
                },
                "REVEL_score": {
                  "type": "number",
                  "nullable": true
                },
                "MutPred_score": {
                  "type": "number",
                  "nullable": true
                },
                "BayesDel_addAF_score": {
                  "type": "number",
                  "nullable": true
                },
                "BayesDel_noAF_score": {
                  "type": "number",
                  "nullable": true
                },
                "VARITY_R_score": {
                  "type": "number",
                  "nullable": true
                },
                "VARITY_ER_score": {
                  "type": "number",
                  "nullable": true
                },
                "VARITY_R_LOO_score": {
                  "type": "number",
                  "nullable": true
                },
                "VARITY_ER_LOO_score": {
                  "type": "number",
                  "nullable": true
                },
                "ESM1b_score": {
                  "type": "number",
                  "nullable": true
                },
                "EVE_score": {
                  "type": "number",
                  "nullable": true
                },
                "AlphaMissense_score": {
                  "type": "number",
                  "nullable": true
                },
                "CADD_raw_score": {
                  "type": "number",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                }
              },
              "required": [
                "_id",
                "name",
                "ref",
                "alt",
                "protein_name",
                "protein_id",
                "gene_name",
                "transcript_id",
                "aapos",
                "hgvsp",
                "refcodon",
                "codonpos",
                "SIFT_score",
                "SIFT4G_score",
                "Polyphen2_HDIV_score",
                "Polyphen2_HVAR_score",
                "VEST4_score",
                "Mcap_score",
                "REVEL_score",
                "MutPred_score",
                "BayesDel_addAF_score",
                "BayesDel_noAF_score",
                "VARITY_R_score",
                "VARITY_ER_score",
                "VARITY_R_LOO_score",
                "VARITY_ER_LOO_score",
                "ESM1b_score",
                "EVE_score",
                "AlphaMissense_score",
                "CADD_raw_score",
                "source",
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
