# `GET /variants/drugs`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/variants_drugs.ts`](../../src/routers/datatypeRouters/edges/variants_drugs.ts)

## Description

Retrieve drugs associated with the query variants from pharmGKB.<br>   Set verbose = true to retrieve full info on the drugs.<br>   Example: variant_id = NC_000001.11:230714139:T:G, <br>   spdi = NC_000001.11:230714139:T:G, <br>   hgvs = NC_000001.11:g.230714140T>G, <br>   rsid = rs5050 (at least one of the variant fields needs to be specified), <br>   ca_id = CA10610220, <br>   region = chr3:186741137-186742238 (maximum length: 10kb), <br>   the following filters on variants-drugs association can be combined for query: <br>   GENCODE_category = coding (or noncoding), <br>   pmid = 20824505, <br>   phenotype_categories = Toxicity. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "drugsFromVariants",
  "description": "Retrieve drugs associated with the query variants from pharmGKB.<br>   Set verbose = true to retrieve full info on the drugs.<br>   Example: variant_id = NC_000001.11:230714139:T:G, <br>   spdi = NC_000001.11:230714139:T:G, <br>   hgvs = NC_000001.11:g.230714140T>G, <br>   rsid = rs5050 (at least one of the variant fields needs to be specified), <br>   ca_id = CA10610220, <br>   region = chr3:186741137-186742238 (maximum length: 10kb), <br>   the following filters on variants-drugs association can be combined for query: <br>   GENCODE_category = coding (or noncoding), <br>   pmid = 20824505, <br>   phenotype_categories = Toxicity. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
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
                "drug": {
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
                        "drug_ontology_terms": {
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
                "_from": {
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
                "_from",
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
