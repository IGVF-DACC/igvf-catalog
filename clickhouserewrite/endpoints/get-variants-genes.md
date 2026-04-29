# `GET /variants/genes`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts)

## Description

Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGFV by internal variant ids.<br>   The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br>     Set verbose = true to retrieve full info on the corresponding variants and genes.<br>     Example: spdi = NC_000001.11:630556:T:C, <br>     hgvs = NC_000001.11:g.630557T>C, <br>     ca_id = CA16774863, <br>     variant_id = NC_000001.11:630556:T:C, <br>     region = chr3:186741137-186742238 (maximum length: 10kb), <br>     log10pvalue = gte:2, <br>     effect_size = lte:0.001, <br>     biosample_term = EFO_0005292, <br>     biological_context = lymphoblastoid cell line, <br>     name = 'modulates expression of' or 'modulates splicing of' <br>     inverse_name = 'expression modulated by' or 'splicing modulated by' <br>     label = eQTL (should pass other parameters such as source along with label), <br>     method = Variant-EFFECTS, <br>     files_fileset = IGVFFI9602ILPC, <br>     source = AFGR. <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesFromVariants",
  "description": "Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGFV by internal variant ids.<br>   The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br>     Set verbose = true to retrieve full info on the corresponding variants and genes.<br>     Example: spdi = NC_000001.11:630556:T:C, <br>     hgvs = NC_000001.11:g.630557T>C, <br>     ca_id = CA16774863, <br>     variant_id = NC_000001.11:630556:T:C, <br>     region = chr3:186741137-186742238 (maximum length: 10kb), <br>     log10pvalue = gte:2, <br>     effect_size = lte:0.001, <br>     biosample_term = EFO_0005292, <br>     biological_context = lymphoblastoid cell line, <br>     name = 'modulates expression of' or 'modulates splicing of' <br>     inverse_name = 'expression modulated by' or 'splicing modulated by' <br>     label = eQTL (should pass other parameters such as source along with label), <br>     method = Variant-EFFECTS, <br>     files_fileset = IGVFFI9602ILPC, <br>     source = AFGR. <br>     The limit parameter controls the page size and can not exceed 500. <br>     Pagination is 0-based.",
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
      "name": "log10pvalue",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "effect_size",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "biosample_term",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "biological_context",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "label",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "eQTL",
          "spliceQTL",
          "variant effect on gene expression"
        ]
      }
    },
    {
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Variant-EFFECTS",
          "eQTL",
          "spliceQTL"
        ]
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
      "name": "source",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "AFGR",
          "EBI",
          "IGVF"
        ]
      }
    },
    {
      "name": "name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "modulates expression of",
          "modulates splicing of"
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
                "gene": {
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
                  ],
                  "nullable": true
                },
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
                  ],
                  "nullable": true
                },
                "intron_chr": {
                  "type": "string",
                  "nullable": true
                },
                "intron_start": {
                  "type": "string",
                  "nullable": true
                },
                "intron_end": {
                  "type": "string",
                  "nullable": true
                },
                "effect_size": {
                  "type": "number",
                  "nullable": true
                },
                "log10pvalue": {
                  "anyOf": [
                    {
                      "type": "number"
                    },
                    {
                      "type": "string"
                    }
                  ],
                  "nullable": true
                },
                "fdr_nlog10": {
                  "type": "number",
                  "nullable": true
                },
                "log2_fold_change": {
                  "type": "number",
                  "nullable": true
                },
                "p_nominal_nlog10": {
                  "type": "number",
                  "nullable": true
                },
                "posterior_inclusion_probability": {
                  "type": "number",
                  "nullable": true
                },
                "standard_error": {
                  "type": "number",
                  "nullable": true
                },
                "z_score": {
                  "type": "number",
                  "nullable": true
                },
                "credible_set_min_r2": {
                  "type": "number",
                  "nullable": true
                },
                "method": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "label": {
                  "type": "string"
                },
                "p_value": {
                  "type": "number",
                  "nullable": true
                },
                "chr": {
                  "type": "string",
                  "nullable": true
                },
                "biological_context": {
                  "type": "string"
                },
                "biosample_term": {
                  "type": "string"
                },
                "study": {
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
                          "type": "string"
                        },
                        "ancestry_initial": {
                          "type": "string",
                          "nullable": true
                        },
                        "ancestry_replication": {
                          "type": "string",
                          "nullable": true
                        },
                        "n_cases": {
                          "type": "string",
                          "nullable": true
                        },
                        "n_initial": {
                          "type": "string",
                          "nullable": true
                        },
                        "n_replication": {
                          "type": "string",
                          "nullable": true
                        },
                        "pmid": {
                          "type": "string",
                          "nullable": true
                        },
                        "pub_author": {
                          "type": "string",
                          "nullable": true
                        },
                        "pub_date": {
                          "type": "string",
                          "nullable": true
                        },
                        "pub_journal": {
                          "type": "string",
                          "nullable": true
                        },
                        "pub_title": {
                          "type": "string",
                          "nullable": true
                        },
                        "has_sumstats": {
                          "type": "string",
                          "nullable": true
                        },
                        "num_assoc_loci": {
                          "type": "string",
                          "nullable": true
                        },
                        "study_source": {
                          "type": "string",
                          "nullable": true
                        },
                        "trait_reported": {
                          "type": "string",
                          "nullable": true
                        },
                        "trait_efos": {
                          "type": "string",
                          "nullable": true
                        },
                        "trait_category": {
                          "type": "string",
                          "nullable": true
                        },
                        "source": {
                          "type": "string"
                        },
                        "study_type": {
                          "type": "string",
                          "nullable": true
                        },
                        "version": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "_id",
                        "name",
                        "ancestry_initial",
                        "ancestry_replication",
                        "n_cases",
                        "n_initial",
                        "n_replication",
                        "pmid",
                        "pub_author",
                        "pub_date",
                        "pub_journal",
                        "pub_title",
                        "has_sumstats",
                        "num_assoc_loci",
                        "study_source",
                        "trait_reported",
                        "trait_efos",
                        "trait_category",
                        "study_type",
                        "version"
                      ],
                      "additionalProperties": false
                    }
                  ],
                  "nullable": true
                },
                "name": {
                  "type": "string",
                  "nullable": true
                },
                "class": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "gene",
                "sequence_variant",
                "source",
                "source_url",
                "label",
                "biological_context",
                "biosample_term"
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
