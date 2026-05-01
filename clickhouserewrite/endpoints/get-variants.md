# `GET /variants`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts)

## Description

Retrieve genetic variants.<br>   Example: organism = Homo sapiens or Mus musculus.<br>   mouse_strain = CAST_EiJ (only for mouse variants). <br>   The examples below are specific to Homo sapiens: <br>   region = chr1:1157520-1158189 (maximum length: 10kb), <br>   GENCODE_category = coding or noncoding (only for human variants), <br>   rsid = rs58658771,  <br>   spdi = NC_000020.11:3658947:A:G, <br>   hgvs = NC_000020.11:g.3658948A>G, <br>   ca_id = CA739473472, <br>   variant_id = NC_000020.11:3658947:A:G. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variants",
  "description": "Retrieve genetic variants.<br>   Example: organism = Homo sapiens or Mus musculus.<br>   mouse_strain = CAST_EiJ (only for mouse variants). <br>   The examples below are specific to Homo sapiens: <br>   region = chr1:1157520-1158189 (maximum length: 10kb), <br>   GENCODE_category = coding or noncoding (only for human variants), <br>   rsid = rs58658771,  <br>   spdi = NC_000020.11:3658947:A:G, <br>   hgvs = NC_000020.11:g.3658948A>G, <br>   ca_id = CA739473472, <br>   variant_id = NC_000020.11:3658947:A:G. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "rsid",
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
      "name": "region",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "GENCODE_category",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "coding",
          "noncoding"
        ]
      }
    },
    {
      "name": "mouse_strain",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "129S1_SvImJ",
          "A_J",
          "CAST_EiJ",
          "NOD_ShiLtJ",
          "NZO_HlLtJ",
          "PWK_PhJ",
          "WSB_EiJ"
        ]
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
                "chr": {
                  "type": "string"
                },
                "pos": {
                  "type": "number"
                },
                "rsid": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "ref": {
                  "type": "string"
                },
                "alt": {
                  "type": "string"
                },
                "spdi": {
                  "type": "string"
                },
                "hgvs": {
                  "type": "string"
                },
                "ca_id": {
                  "type": "string",
                  "nullable": true
                },
                "strain": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "qual": {
                  "type": "string",
                  "nullable": true
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                },
                "annotations": {
                  "type": "object",
                  "properties": {
                    "bravo_af": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_total": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_afr": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_afr_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_afr_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_ami": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_ami_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_ami_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_amr": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_amr_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_amr_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_asj": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_asj_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_asj_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_eas": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_eas_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_eas_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_fin": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_fin_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_fin_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_nfe": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_nfe_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_nfe_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_oth": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_oth_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_oth_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_sas": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_sas_male": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_sas_female": {
                      "type": "number",
                      "nullable": true
                    },
                    "gnomad_af_raw": {
                      "type": "number",
                      "nullable": true
                    },
                    "GENCODE_category": {
                      "type": "string",
                      "nullable": true
                    },
                    "funseq_description": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "additionalProperties": false,
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "organism": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "chr",
                "pos",
                "ref",
                "alt",
                "annotations",
                "source",
                "source_url",
                "organism"
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
