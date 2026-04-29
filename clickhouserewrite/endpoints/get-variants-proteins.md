# `GET /variants/proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_proteins.ts`](../../src/routers/datatypeRouters/edges/variants_proteins.ts)

## Description

Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br>    allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying variants, and predicted allele specific binding from SEMpl.<br>   Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br>   Example: variant_id = NC_000020.11:4814342:G:A, <br>   spdi = NC_000017.11:7166092:G:A, <br>   hgvs = NC_000017.11:g.7166093G>A, <br>   rsid = rs186021206,<br>   ca_id = CA14813418, <br>   region = chr17:7166090-7166095 (maximum length: 10kb), <br>   organism = Homo sapiens, <br>   label = pQTL (or allele-specific binding), <br>   name = 'modulates binding of' or 'associated with levels of',<br>   inverse_name = 'binding modulated by' or 'level associated with',<br>   method = SEMVAR, <br>   files_fileset = IGVFFI0183ELIK, <br>   source = UKB. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "proteinsFromVariants",
  "description": "Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br>    allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying variants, and predicted allele specific binding from SEMpl.<br>   Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br>   Example: variant_id = NC_000020.11:4814342:G:A, <br>   spdi = NC_000017.11:7166092:G:A, <br>   hgvs = NC_000017.11:g.7166093G>A, <br>   rsid = rs186021206,<br>   ca_id = CA14813418, <br>   region = chr17:7166090-7166095 (maximum length: 10kb), <br>   organism = Homo sapiens, <br>   label = pQTL (or allele-specific binding), <br>   name = 'modulates binding of' or 'associated with levels of',<br>   inverse_name = 'binding modulated by' or 'level associated with',<br>   method = SEMVAR, <br>   files_fileset = IGVFFI0183ELIK, <br>   source = UKB. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
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
      "name": "label",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "allele-specific binding",
          "pQTL",
          "predicted allele-specific binding"
        ]
      }
    },
    {
      "name": "source",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "ADASTRA",
          "GVATdb",
          "IGVF",
          "UKB"
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
          "ADASTRA",
          "GVATdb",
          "SEMVAR",
          "pQTL"
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
      "name": "name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "associated with levels of",
          "modulates binding of"
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
                "sequence_variant": {
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
                "protein_complex": {
                  "anyOf": [
                    {
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
                            "uniprot_names": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "nullable": true
                            },
                            "uniprot_full_names": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "nullable": true
                            },
                            "uniprot_ids": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "nullable": true
                            },
                            "MANE_Select": {
                              "type": "boolean",
                              "nullable": true
                            },
                            "organism": {
                              "type": "string"
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
                            "organism",
                            "source",
                            "source_url"
                          ],
                          "additionalProperties": false
                        }
                      ]
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
                        "alias": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "molecules": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "evidence_code": {
                          "type": "string",
                          "nullable": true
                        },
                        "experimental_evidence": {
                          "type": "string",
                          "nullable": true
                        },
                        "description": {
                          "type": "string",
                          "nullable": true
                        },
                        "complex_assembly": {
                          "anyOf": [
                            {
                              "type": "string"
                            },
                            {
                              "type": "array",
                              "items": {
                                "type": "string"
                              }
                            }
                          ],
                          "nullable": true
                        },
                        "complex_source": {
                          "type": "string",
                          "nullable": true
                        },
                        "reactome_xref": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
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
                        "source",
                        "source_url"
                      ],
                      "additionalProperties": false
                    }
                  ]
                },
                "biosample_term": {
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
                  ],
                  "nullable": true
                },
                "biological_context": {
                  "type": "string",
                  "nullable": true
                },
                "regulatory_type": {
                  "type": "string",
                  "nullable": true
                },
                "class": {
                  "type": "string",
                  "nullable": true
                },
                "label": {
                  "type": "string",
                  "nullable": true
                },
                "name": {
                  "type": "string"
                },
                "method": {
                  "type": "string",
                  "nullable": true
                },
                "files_filesets": {
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
                "is_complex": {
                  "type": "boolean"
                },
                "score": {
                  "type": "number",
                  "nullable": true
                },
                "fdrp_bh_ref": {
                  "type": "string",
                  "nullable": true
                },
                "fdrp_bh_alt": {
                  "type": "string",
                  "nullable": true
                },
                "motif": {
                  "type": "string",
                  "nullable": true
                },
                "motif_fc": {
                  "type": "string",
                  "nullable": true
                },
                "beta": {
                  "type": "number",
                  "nullable": true
                },
                "se": {
                  "type": "number",
                  "nullable": true
                },
                "gene": {
                  "type": "string",
                  "nullable": true
                },
                "gene_consequence": {
                  "type": "string",
                  "nullable": true
                },
                "log10pvalue": {
                  "type": "number",
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
                "variant_effect_score": {
                  "type": "number",
                  "nullable": true
                },
                "SEMpl_annotation": {
                  "type": "string",
                  "nullable": true
                },
                "SEMpl_baseline": {
                  "type": "number",
                  "nullable": true
                },
                "alt_score": {
                  "type": "number",
                  "nullable": true
                },
                "ref_score": {
                  "type": "number",
                  "nullable": true
                },
                "relative_binding_affinity": {
                  "type": "number",
                  "nullable": true
                },
                "effect_on_binding": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "name",
                "is_complex"
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
