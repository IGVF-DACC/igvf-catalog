# `GET /variants/freq`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts)

## Description

Retrieve genetic variants within a genomic region by frequencies.<br>    Example: region = chr3:186741137-186742238 (maximum length: 10kb), <br>    source = bravo_af, <br>    GENCODE_category = coding (or noncoding), <br>    spdi = NC_000003.12:186741142:G:A, <br>    hgvs = NC_000003.12:g.186741143G>A, <br>    rsid = rs1720801112, <br>    ca_id = CA739473472, <br>    minimum_af: 0, <br>    maximum_af:0.8. <br>    Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantByFrequencySource",
  "description": "Retrieve genetic variants within a genomic region by frequencies.<br>    Example: region = chr3:186741137-186742238 (maximum length: 10kb), <br>    source = bravo_af, <br>    GENCODE_category = coding (or noncoding), <br>    spdi = NC_000003.12:186741142:G:A, <br>    hgvs = NC_000003.12:g.186741143G>A, <br>    rsid = rs1720801112, <br>    ca_id = CA739473472, <br>    minimum_af: 0, <br>    maximum_af:0.8. <br>    Pagination is 0-based.",
  "parameters": [
    {
      "name": "source",
      "in": "query",
      "required": true,
      "schema": {
        "type": "string",
        "enum": [
          "bravo_af",
          "gnomad_af_total",
          "gnomad_af_afr",
          "gnomad_af_afr_female",
          "gnomad_af_afr_male",
          "gnomad_af_ami",
          "gnomad_af_ami_female",
          "gnomad_af_ami_male",
          "gnomad_af_amr",
          "gnomad_af_amr_female",
          "gnomad_af_amr_male",
          "gnomad_af_asj",
          "gnomad_af_asj_female",
          "gnomad_af_asj_male",
          "gnomad_af_eas",
          "gnomad_af_eas_female",
          "gnomad_af_eas_male",
          "gnomad_af_female",
          "gnomad_af_fin",
          "gnomad_af_fin_female",
          "gnomad_af_fin_male",
          "gnomad_af_male",
          "gnomad_af_nfe",
          "gnomad_af_nfe_female",
          "gnomad_af_nfe_male",
          "gnomad_af_oth",
          "gnomad_af_oth_female",
          "gnomad_af_oth_male",
          "gnomad_af_sas",
          "gnomad_af_sas_male",
          "gnomad_af_sas_female",
          "gnomad_af_raw"
        ]
      }
    },
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
      "name": "minimum_af",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number",
        "default": 0
      }
    },
    {
      "name": "maximum_af",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number",
        "default": 1
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
