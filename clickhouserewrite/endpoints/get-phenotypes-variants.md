# `GET /phenotypes/variants`

**Status:** ✅ ClickHouse-ported

**Router file:** [`src/routers/datatypeRouters/edges/variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/variants_phenotypes.ts)

## Description

Retrieve variant-trait pairs from GWAS by phenotypes.<br>   The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br>   Set verbose = true to retrieve full info on the studies.<br>   Example: phenotype ID = EFO_0007937, <br>   phenotype_name = cell survival, <br>   log10pvalue = gte:5, <br>   method = SGE, <br>   class = observed data, <br>   label = protein variant effect, <br>   files_fileset = IGVFFI0332UGDD. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "variantsFromPhenotypes",
  "description": "Retrieve variant-trait pairs from GWAS by phenotypes.<br>   The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br>   Set verbose = true to retrieve full info on the studies.<br>   Example: phenotype ID = EFO_0007937, <br>   phenotype_name = cell survival, <br>   log10pvalue = gte:5, <br>   method = SGE, <br>   class = observed data, <br>   label = protein variant effect, <br>   files_fileset = IGVFFI0332UGDD. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "phenotype_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "phenotype_name",
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
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "GWAS",
          "SGE",
          "cV2F"
        ]
      }
    },
    {
      "name": "label",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "GWAS",
          "predicted variant effect on phenotype",
          "protein variant effect"
        ]
      }
    },
    {
      "name": "class",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "observed data",
          "prediction"
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
          "IGVF",
          "OpenTargets"
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
              "anyOf": [
                {
                  "type": "object",
                  "properties": {
                    "rsid": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "nullable": true
                    },
                    "phenotype_id": {
                      "type": "string",
                      "nullable": true
                    },
                    "phenotype_term": {
                      "type": "string",
                      "nullable": true
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
                      ]
                    },
                    "log10pvalue": {
                      "type": "number",
                      "nullable": true
                    },
                    "p_val": {
                      "type": "number",
                      "nullable": true
                    },
                    "beta": {
                      "type": "number",
                      "nullable": true
                    },
                    "beta_ci_lower": {
                      "type": "number",
                      "nullable": true
                    },
                    "beta_ci_upper": {
                      "type": "number",
                      "nullable": true
                    },
                    "oddsr_ci_lower": {
                      "type": "number",
                      "nullable": true
                    },
                    "oddsr_ci_upper": {
                      "type": "number",
                      "nullable": true
                    },
                    "lead_chrom": {
                      "type": "string",
                      "nullable": true
                    },
                    "lead_pos": {
                      "type": "number",
                      "nullable": true
                    },
                    "lead_ref": {
                      "type": "string",
                      "nullable": true
                    },
                    "lead_alt": {
                      "type": "string",
                      "nullable": true
                    },
                    "direction": {
                      "type": "string",
                      "nullable": true
                    },
                    "source": {
                      "type": "string",
                      "default": "OpenTargets"
                    },
                    "source_url": {
                      "type": "string",
                      "nullable": true
                    },
                    "class": {
                      "type": "string",
                      "nullable": true
                    },
                    "method": {
                      "type": "string",
                      "nullable": true
                    },
                    "label": {
                      "type": "string",
                      "nullable": true
                    },
                    "version": {
                      "type": "string",
                      "default": "October 2022 (22.10)"
                    },
                    "name": {
                      "type": "string"
                    },
                    "variant": {
                      "anyOf": [
                        {
                          "type": "string"
                        },
                        {
                          "type": "object",
                          "properties": {
                            "chr": {
                              "type": "string"
                            },
                            "pos": {
                              "type": "number"
                            },
                            "ref": {
                              "type": "string"
                            },
                            "alt": {
                              "type": "string"
                            },
                            "rsid": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "nullable": true
                            },
                            "spdi": {
                              "type": "string",
                              "nullable": true
                            },
                            "hgvs": {
                              "type": "string",
                              "nullable": true
                            },
                            "ca_id": {
                              "type": "string",
                              "nullable": true
                            },
                            "_id": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "chr",
                            "pos",
                            "ref",
                            "alt"
                          ],
                          "additionalProperties": false
                        }
                      ]
                    }
                  },
                  "required": [
                    "phenotype_id",
                    "phenotype_term",
                    "log10pvalue",
                    "p_val",
                    "beta",
                    "beta_ci_lower",
                    "beta_ci_upper",
                    "oddsr_ci_lower",
                    "oddsr_ci_upper",
                    "lead_chrom",
                    "lead_pos",
                    "lead_ref",
                    "lead_alt",
                    "direction",
                    "name",
                    "variant"
                  ],
                  "additionalProperties": false
                },
                {
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    },
                    "biological_context": {
                      "type": "string",
                      "nullable": true
                    },
                    "source": {
                      "type": "string"
                    },
                    "source_url": {
                      "type": "string"
                    },
                    "score": {
                      "type": "number",
                      "nullable": true
                    },
                    "method": {
                      "type": "string",
                      "nullable": true
                    },
                    "class": {
                      "type": "string",
                      "nullable": true
                    },
                    "files_filesets": {
                      "type": "string",
                      "nullable": true
                    },
                    "phenotype_term": {
                      "type": "string",
                      "nullable": true
                    },
                    "variant": {
                      "anyOf": [
                        {
                          "type": "string"
                        },
                        {
                          "type": "object",
                          "properties": {
                            "chr": {
                              "type": "string"
                            },
                            "pos": {
                              "type": "number"
                            },
                            "ref": {
                              "type": "string"
                            },
                            "alt": {
                              "type": "string"
                            },
                            "rsid": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "nullable": true
                            },
                            "spdi": {
                              "type": "string",
                              "nullable": true
                            },
                            "hgvs": {
                              "type": "string",
                              "nullable": true
                            },
                            "ca_id": {
                              "type": "string",
                              "nullable": true
                            },
                            "_id": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "chr",
                            "pos",
                            "ref",
                            "alt"
                          ],
                          "additionalProperties": false
                        }
                      ]
                    },
                    "phenotype_id": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "name",
                    "source",
                    "source_url",
                    "score",
                    "method",
                    "files_filesets",
                    "phenotype_term",
                    "variant",
                    "phenotype_id"
                  ],
                  "additionalProperties": false
                }
              ]
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
