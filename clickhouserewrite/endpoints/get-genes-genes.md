# `GET /genes/genes`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_genes.ts`](../../src/routers/datatypeRouters/edges/genes_genes.ts)

## Description

Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID. <br>   The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br>     Example: organism = Homo sapiens or Mus musculus, <br>     source = COXPRESdb, <br>     interaction_type = dosage growth defect (sensu BioGRID), <br>     gene_id = ENSG00000121410, <br>     hgnc_id = HGNC:5, <br>     gene_name = A1BG, <br>     alias = HYST2477, <br>     z_score = gt:4, <br>     label = genetic interference, <br>     method = COXPRESdb, <br>     name = 'interacts with' or 'coexpressed with' <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesGenes",
  "description": "Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID. <br>   The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br>     Example: organism = Homo sapiens or Mus musculus, <br>     source = COXPRESdb, <br>     interaction_type = dosage growth defect (sensu BioGRID), <br>     gene_id = ENSG00000121410, <br>     hgnc_id = HGNC:5, <br>     gene_name = A1BG, <br>     alias = HYST2477, <br>     z_score = gt:4, <br>     label = genetic interference, <br>     method = COXPRESdb, <br>     name = 'interacts with' or 'coexpressed with' <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.",
  "parameters": [
    {
      "name": "gene_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "hgnc_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "gene_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "alias",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "z_score",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "interaction_type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "dosage growth defect (sensu BioGRID)",
          "dosage lethality (sensu BioGRID)",
          "dosage rescue (sensu BioGRID)",
          "negative genetic interaction (sensu BioGRID)",
          "phenotypic enhancement (sensu BioGRID)",
          "phenotypic suppression (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID)",
          "synthetic growth defect (sensu BioGRID)",
          "synthetic lethality (sensu BioGRID)",
          "synthetic rescue (sensu BioGRID)"
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
          "co-expression",
          "genetic interference"
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
          "COXPRESdb",
          "dosage growth defect (sensu BioGRID)",
          "dosage lethality (sensu BioGRID)",
          "dosage lethality (sensu BioGRID), phenotypic enhancement (sensu BioGRID)",
          "dosage lethality (sensu BioGRID), synthetic lethality (sensu BioGRID)",
          "dosage rescue (sensu BioGRID)",
          "dosage rescue (sensu BioGRID), phenotypic enhancement (sensu BioGRID)",
          "dosage rescue (sensu BioGRID), synthetic growth defect (sensu BioGRID)",
          "negative genetic interaction (sensu BioGRID)",
          "negative genetic interaction (sensu BioGRID), synthetic growth defect (sensu BioGRID)",
          "negative genetic interaction (sensu BioGRID), synthetic lethality (sensu BioGRID)",
          "negative genetic interaction (sensu BioGRID), synthetic lethality (sensu BioGRID), synthetic growth defect (sensu BioGRID)",
          "phenotypic enhancement (sensu BioGRID)",
          "phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID)",
          "phenotypic enhancement (sensu BioGRID), synthetic growth defect (sensu BioGRID)",
          "phenotypic enhancement (sensu BioGRID), synthetic lethality (sensu BioGRID)",
          "phenotypic suppression (sensu BioGRID)",
          "phenotypic suppression (sensu BioGRID), negative genetic interaction (sensu BioGRID)",
          "phenotypic suppression (sensu BioGRID), phenotypic enhancement (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID), negative genetic interaction (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID), phenotypic enhancement (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID), synthetic lethality (sensu BioGRID)",
          "positive genetic interaction (sensu BioGRID), synthetic rescue (sensu BioGRID)",
          "synthetic growth defect (sensu BioGRID)",
          "synthetic growth defect (sensu BioGRID), phenotypic enhancement (sensu BioGRID)",
          "synthetic haploinsufficiency (sensu BioGRID)",
          "synthetic haploinsufficiency (sensu BioGRID), dosage rescue (sensu BioGRID)",
          "synthetic haploinsufficiency (sensu BioGRID), phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID)",
          "synthetic lethality (sensu BioGRID)",
          "synthetic lethality (sensu BioGRID), phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID)",
          "synthetic lethality (sensu BioGRID), synthetic growth defect (sensu BioGRID)",
          "synthetic rescue (sensu BioGRID)"
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
          "BioGRID",
          "COXPRESdb"
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
          "coexpressed with",
          "interacts with"
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
                "gene 1": {
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
                    }
                  ]
                },
                "gene 2": {
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
                    }
                  ]
                },
                "z_score": {
                  "type": "number"
                },
                "detection_method": {
                  "type": "string"
                },
                "detection_method_code": {
                  "type": "string"
                },
                "interaction_type": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "interaction_type_code": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "confidence_value_biogrid": {
                  "type": "number",
                  "nullable": true
                },
                "confidence_value_intact": {
                  "type": "number",
                  "nullable": true
                },
                "pmids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "label": {
                  "type": "string"
                },
                "method": {
                  "type": "string"
                },
                "class": {
                  "type": "string"
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
                "gene 1",
                "gene 2",
                "label",
                "method",
                "class",
                "source",
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
