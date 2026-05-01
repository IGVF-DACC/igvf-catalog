# `GET /genomic-elements/biosamples`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts)

## Description

Retrieve MPRA experiments by querying positions of genomic elements. <br>   Set verbose = true to retrieve full info on the cell ontology terms. <br>   Example: region_type = tested elements, region = chr10:100038743-100038963. <br>   You can also filter out by study file, e.g., files_fileset = ENCFF475FKV; method, e.g MPRA; and source, e.g. IGVF or ENCODE. <br>   The limit parameter controls the page size and can not exceed 50. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "biosamplesFromGenomicElements",
  "description": "Retrieve MPRA experiments by querying positions of genomic elements. <br>   Set verbose = true to retrieve full info on the cell ontology terms. <br>   Example: region_type = tested elements, region = chr10:100038743-100038963. <br>   You can also filter out by study file, e.g., files_fileset = ENCFF475FKV; method, e.g MPRA; and source, e.g. IGVF or ENCODE. <br>   The limit parameter controls the page size and can not exceed 50. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "region",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "region_type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "accessible dna elements",
          "candidate cis regulatory element",
          "tested elements"
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
          "ENCODE",
          "IGVF"
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
          "MPRA"
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
                "log2FC": {
                  "type": "number",
                  "nullable": true
                },
                "strand": {
                  "type": "string",
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
                "DNA_count": {
                  "type": "number",
                  "nullable": true
                },
                "RNA_count": {
                  "type": "number",
                  "nullable": true
                },
                "significant": {
                  "type": "boolean",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "genomic_element": {
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
                        "start": {
                          "type": "number"
                        },
                        "end": {
                          "type": "number"
                        },
                        "name": {
                          "type": "string"
                        },
                        "method": {
                          "type": "string",
                          "nullable": true
                        },
                        "source_annotation": {
                          "type": "string",
                          "nullable": true
                        },
                        "type": {
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
                        "chr",
                        "start",
                        "end",
                        "name",
                        "source_annotation",
                        "type",
                        "source",
                        "source_url"
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
                "name": {
                  "type": "string"
                },
                "class": {
                  "type": "string"
                },
                "method": {
                  "type": "string"
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "log2FC",
                "strand",
                "p_value",
                "fdr",
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
