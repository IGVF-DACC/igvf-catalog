# `GET /variants/biosamples`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_biosamples.ts`](../../src/routers/datatypeRouters/edges/variants_biosamples.ts)

## Description

Retrieve data from STARR-seq, BlueSTARR, and MPRA for a given variant.<br>   Example: variant_id = NC_000001.11:14772:C:T,<br>   spdi = NC_000001.11:14772:C:T, <br>   hgvs = NC_000001.11:g.14773C>T, <br>   rsid = rs1234567890, <br>   ca_id = CA10655131, <br>   region = chr1:15563-15567 (maximum length: 10kb), <br>   organism = Homo sapiens, <br>   files_fileset = IGVFFI1323RCIE, <br>   element_id = candidate_cis_regulatory_element_chr5_1778763_1779094_GRCh38_ENCFF420VPZ, <br>   significant = true, <br>   method = STARR-seq. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "biosamplesFromVariants",
  "description": "Retrieve data from STARR-seq, BlueSTARR, and MPRA for a given variant.<br>   Example: variant_id = NC_000001.11:14772:C:T,<br>   spdi = NC_000001.11:14772:C:T, <br>   hgvs = NC_000001.11:g.14773C>T, <br>   rsid = rs1234567890, <br>   ca_id = CA10655131, <br>   region = chr1:15563-15567 (maximum length: 10kb), <br>   organism = Homo sapiens, <br>   files_fileset = IGVFFI1323RCIE, <br>   element_id = candidate_cis_regulatory_element_chr5_1778763_1779094_GRCh38_ENCFF420VPZ, <br>   significant = true, <br>   method = STARR-seq. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
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
      "name": "files_fileset",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "BlueSTARR",
          "MPRA",
          "STARR-seq"
        ]
      }
    },
    {
      "name": "element_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "significant",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "true",
          "false"
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
                "variant": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
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
                  ]
                },
                "biosample": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "object",
                      "properties": {
                        "uri": {
                          "type": "string"
                        },
                        "term_id": {
                          "type": "string"
                        },
                        "name": {
                          "type": "string"
                        },
                        "synonyms": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "description": {
                          "type": "string",
                          "nullable": true
                        },
                        "source": {
                          "type": "string"
                        },
                        "subontology": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_url": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "uri",
                        "term_id",
                        "name"
                      ],
                      "additionalProperties": false
                    }
                  ]
                },
                "genomic_element": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "object",
                      "properties": {
                        "_id": {
                          "type": "string"
                        },
                        "name": {
                          "type": "string",
                          "nullable": true
                        },
                        "chr": {
                          "type": "string",
                          "nullable": true
                        },
                        "start": {
                          "type": "number",
                          "nullable": true
                        },
                        "end": {
                          "type": "number",
                          "nullable": true
                        },
                        "type": {
                          "type": "string",
                          "nullable": true
                        },
                        "source": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_url": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_annotation": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "_id"
                      ],
                      "additionalProperties": false
                    }
                  ],
                  "nullable": true
                },
                "log2FoldChange": {
                  "type": "number",
                  "nullable": true
                },
                "DNA_count_ref": {
                  "type": "number",
                  "nullable": true
                },
                "DNA_count_alt": {
                  "type": "number",
                  "nullable": true
                },
                "RNA_count_ref": {
                  "type": "number",
                  "nullable": true
                },
                "RNA_count_alt": {
                  "type": "number",
                  "nullable": true
                },
                "postProbEffect": {
                  "type": "number",
                  "nullable": true
                },
                "CI_lower_95": {
                  "type": "number",
                  "nullable": true
                },
                "CI_upper_95": {
                  "type": "number",
                  "nullable": true
                },
                "significant": {
                  "type": "boolean",
                  "nullable": true
                },
                "p_value": {
                  "type": "number",
                  "nullable": true
                },
                "fdr": {
                  "type": "number",
                  "nullable": true
                },
                "label": {
                  "type": "string"
                },
                "method": {
                  "type": "string"
                },
                "class": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "label",
                "method",
                "source",
                "source_url",
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
