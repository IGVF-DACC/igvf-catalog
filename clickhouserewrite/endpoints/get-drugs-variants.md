# `GET /drugs/variants`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_drugs.ts`](../../src/routers/datatypeRouters/edges/variants_drugs.ts)

## Description

Retrieve variants associated with the query drugs from pharmGKB.<br>   Set verbose = true to retrieve full info on the variants. <br>   Example: drug_id = PA448497, <br>   drug_name = aspirin, (at least one of the drug fields needs to be specified), <br>   the following filters on variants-drugs association can be combined for query: <br>   pmid = 20824505, <br>   phenotype_categories = Toxicity. <br>   organism = Homo sapiens. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromDrugs",
  "description": "Retrieve variants associated with the query drugs from pharmGKB.<br>   Set verbose = true to retrieve full info on the variants. <br>   Example: drug_id = PA448497, <br>   drug_name = aspirin, (at least one of the drug fields needs to be specified), <br>   the following filters on variants-drugs association can be combined for query: <br>   pmid = 20824505, <br>   phenotype_categories = Toxicity. <br>   organism = Homo sapiens. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "drug_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "drug_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "phenotype_categories",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Dosage",
          "Efficacy",
          "Metabolism/PK",
          "Other",
          "PD",
          "Toxicity"
        ]
      }
    },
    {
      "name": "pmid",
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
                "sequence_variant": {
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
                "_to": {
                  "type": "string"
                },
                "gene_symbol": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "pmid": {
                  "type": "string"
                },
                "study_parameters": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "study_parameter_id": {
                        "type": "string"
                      },
                      "study_type": {
                        "type": "string"
                      },
                      "study_cases": {
                        "type": "string"
                      },
                      "study_controls": {
                        "type": "string"
                      },
                      "p-value": {
                        "type": "string"
                      },
                      "biogeographical_groups": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "study_parameter_id"
                    ],
                    "additionalProperties": false
                  }
                },
                "phenotype_categories": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "name": {
                  "type": "string"
                }
              },
              "required": [
                "_to",
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
