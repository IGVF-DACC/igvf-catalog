# `GET /variants/variant-ld`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_variants.ts`](../../src/routers/datatypeRouters/edges/variants_variants.ts)

## Description

Retrieve genetic variants in linkage disequilibrium (LD).<br>    The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br>     Set verbose = true to retrieve full info on the variants.<br>      Example: variant_id = NC_000011.10:9083634:A:T,<br>     chr = chr11, position (zero base) = 9083634, <br>     spdi = NC_000011.10:9083634:A:T, <br>     hgvs = NC_000011.10:g.9083635A>T, <br>     rsid = rs60960132, <br>     ca_id = CA217534780, <br>     region = chr17:7166090-7166095 (maximum length: 10kb), <br>     r2 = gte:0.8, <br>     d_prime = gt:0.9, <br>     ancestry = EUR. <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromVariantID",
  "description": "Retrieve genetic variants in linkage disequilibrium (LD).<br>    The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br>     Set verbose = true to retrieve full info on the variants.<br>      Example: variant_id = NC_000011.10:9083634:A:T,<br>     chr = chr11, position (zero base) = 9083634, <br>     spdi = NC_000011.10:9083634:A:T, <br>     hgvs = NC_000011.10:g.9083635A>T, <br>     rsid = rs60960132, <br>     ca_id = CA217534780, <br>     region = chr17:7166090-7166095 (maximum length: 10kb), <br>     r2 = gte:0.8, <br>     d_prime = gt:0.9, <br>     ancestry = EUR. <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.",
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
      "name": "r2",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "d_prime",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "ancestry",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "AFR",
          "EAS",
          "EUR",
          "SAS"
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
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
      }
    },
    {
      "name": "verbose",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "true",
          "false"
        ],
        "default": "false"
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
                "chr": {
                  "type": "string",
                  "nullable": true
                },
                "ancestry": {
                  "type": "string",
                  "nullable": true
                },
                "d_prime": {
                  "type": "number",
                  "nullable": true
                },
                "r2": {
                  "type": "number",
                  "nullable": true
                },
                "label": {
                  "type": "string"
                },
                "variant_1_base_pair": {
                  "type": "string"
                },
                "variant_1_rsid": {
                  "type": "string"
                },
                "variant_2_base_pair": {
                  "type": "string"
                },
                "variant_2_rsid": {
                  "type": "string"
                },
                "variant_1_pos": {
                  "type": "number",
                  "nullable": true
                },
                "variant_1_spdi": {
                  "type": "string",
                  "nullable": true
                },
                "variant_1_hgvs": {
                  "type": "string",
                  "nullable": true
                },
                "variant_2_pos": {
                  "type": "number",
                  "nullable": true
                },
                "variant_2_spdi": {
                  "type": "string",
                  "nullable": true
                },
                "variant_2_hgvs": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "sequence_variant": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
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
                          "filter": {
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
                  ]
                },
                "name": {
                  "type": "string"
                }
              },
              "required": [
                "chr",
                "ancestry",
                "d_prime",
                "r2",
                "label",
                "variant_1_base_pair",
                "variant_1_rsid",
                "variant_2_base_pair",
                "variant_2_rsid",
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
