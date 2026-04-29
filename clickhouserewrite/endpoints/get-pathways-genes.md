# `GET /pathways/genes`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genes_pathways.ts`](../../src/routers/datatypeRouters/edges/genes_pathways.ts)

## Description

Retrieve genes from pathways.<br>   Set verbose = true to retrieve full info on the genes. <br>   Example: id = R-HSA-164843, <br>   name = 2-LTR circle formation, <br>   name_aliases = 2-LTR circle formation, <br>   disease_ontology_terms = DOID_526, <br>   go_biological_process = GO_0006015. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesFromPathways",
  "description": "Retrieve genes from pathways.<br>   Set verbose = true to retrieve full info on the genes. <br>   Example: id = R-HSA-164843, <br>   name = 2-LTR circle formation, <br>   name_aliases = 2-LTR circle formation, <br>   disease_ontology_terms = DOID_526, <br>   go_biological_process = GO_0006015. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "pathway_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "pathway_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "name_aliases",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "disease_ontology_terms",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "go_biological_process",
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
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "orgnism": {
                  "type": "string"
                },
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
                  ]
                },
                "pathway": {
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
                        "organism": {
                          "type": "string"
                        },
                        "source": {
                          "type": "string"
                        },
                        "source_url": {
                          "type": "string"
                        },
                        "id_version": {
                          "type": "string"
                        },
                        "is_in_disease": {
                          "type": "boolean"
                        },
                        "name_aliases": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        },
                        "is_top_level_pathway": {
                          "type": "boolean"
                        },
                        "disease_ontology_terms": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "go_biological_process": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "_id",
                        "name",
                        "organism",
                        "source",
                        "source_url",
                        "id_version",
                        "is_in_disease",
                        "name_aliases",
                        "is_top_level_pathway",
                        "disease_ontology_terms",
                        "go_biological_process"
                      ],
                      "additionalProperties": false
                    }
                  ]
                },
                "name": {
                  "type": "string"
                }
              },
              "required": [
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
