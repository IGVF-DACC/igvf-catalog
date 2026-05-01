# `GET /enhancer-gene-predictions`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/enhancer_genes.ts`](../../src/routers/datatypeRouters/edges/enhancer_genes.ts)

## Description

Retrieve genomic elements and gene pairs by querying genomic elements.<br>   Region is required. Example region = chr1:903900-904900;  source_annotation = enhancer. <br> <br>   You can further filter the results by biosample. For example: <br>   biosample_name = placenta from ENCDO091OEF. <br>   It is also possible to filter by a specific study fileset: <br>   files_fileset = ENCFF968BZL. <br>   And by method, e.g CRISPR FACS screen. <br>   Filters on source, region_type and source_annotation work only in specific combinations based on data availability. <br>   For example: <br>   1. source = ENCODE_EpiRaction, <br>    region_type = accessible dna elements; <br>    source_annotation = enhancer. <br>   2. source = ENCODE-E2G-DNaseOnly and ENCODE-E2G-Full, <br>    region_type = accessible dna elements; <br>    source_annotation = enhancer. <br>   3. source = ENCODE-E2G-CRISPR, region_type = tested elements <br>   [Note: the enhancers list includes all elements that were found to be positive (with significant = True) <br>   for any tested gene while the tested elements lists all the elements ever tested but found to be negative (with significant = False) for all tested genes] ; <br>   source_annotation = enhancer (positive cases) or negative control (negative cases). <br>  Set verbose = true to retrieve full info on the genes, genomic element and biosamples.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "enhancerGenePredictions",
  "description": "Retrieve genomic elements and gene pairs by querying genomic elements.<br>   Region is required. Example region = chr1:903900-904900;  source_annotation = enhancer. <br> <br>   You can further filter the results by biosample. For example: <br>   biosample_name = placenta from ENCDO091OEF. <br>   It is also possible to filter by a specific study fileset: <br>   files_fileset = ENCFF968BZL. <br>   And by method, e.g CRISPR FACS screen. <br>   Filters on source, region_type and source_annotation work only in specific combinations based on data availability. <br>   For example: <br>   1. source = ENCODE_EpiRaction, <br>    region_type = accessible dna elements; <br>    source_annotation = enhancer. <br>   2. source = ENCODE-E2G-DNaseOnly and ENCODE-E2G-Full, <br>    region_type = accessible dna elements; <br>    source_annotation = enhancer. <br>   3. source = ENCODE-E2G-CRISPR, region_type = tested elements <br>   [Note: the enhancers list includes all elements that were found to be positive (with significant = True) <br>   for any tested gene while the tested elements lists all the elements ever tested but found to be negative (with significant = False) for all tested genes] ; <br>   source_annotation = enhancer (positive cases) or negative control (negative cases). <br>  Set verbose = true to retrieve full info on the genes, genomic element and biosamples.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "CRISPR screen",
          "ENCODE-rE2G",
          "Perturb-seq"
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
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    },
                    "_id": {
                      "type": "string"
                    },
                    "start": {
                      "type": "number"
                    },
                    "end": {
                      "type": "number"
                    },
                    "chr": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "name",
                    "_id",
                    "start",
                    "end",
                    "chr"
                  ],
                  "additionalProperties": false
                },
                "elements": {
                  "anyOf": [
                    {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": {
                            "type": "string"
                          },
                          "cell_type": {
                            "type": "string",
                            "nullable": true
                          },
                          "score": {
                            "type": "number",
                            "nullable": true
                          },
                          "model": {
                            "type": "string",
                            "nullable": true
                          },
                          "dataset": {
                            "type": "string",
                            "nullable": true
                          },
                          "element_type": {
                            "type": "string",
                            "nullable": true
                          },
                          "element_chr": {
                            "type": "string",
                            "nullable": true
                          },
                          "element_start": {
                            "type": "number",
                            "nullable": true
                          },
                          "element_end": {
                            "type": "number",
                            "nullable": true
                          },
                          "name": {
                            "type": "string"
                          },
                          "method": {
                            "type": "string"
                          },
                          "class": {
                            "type": "string"
                          },
                          "files_filesets": {
                            "type": "string",
                            "nullable": true
                          }
                        },
                        "required": [
                          "id",
                          "name"
                        ],
                        "additionalProperties": false
                      }
                    },
                    {
                      "type": "object",
                      "properties": {
                        "id": {
                          "type": "string"
                        },
                        "cell_type": {
                          "type": "string",
                          "nullable": true
                        },
                        "score": {
                          "type": "number",
                          "nullable": true
                        },
                        "model": {
                          "type": "string",
                          "nullable": true
                        },
                        "dataset": {
                          "type": "string",
                          "nullable": true
                        },
                        "element_type": {
                          "type": "string",
                          "nullable": true
                        },
                        "element_chr": {
                          "type": "string",
                          "nullable": true
                        },
                        "element_start": {
                          "type": "number",
                          "nullable": true
                        },
                        "element_end": {
                          "type": "number",
                          "nullable": true
                        },
                        "name": {
                          "type": "string"
                        },
                        "method": {
                          "type": "string"
                        },
                        "class": {
                          "type": "string"
                        },
                        "files_filesets": {
                          "type": "string",
                          "nullable": true
                        }
                      },
                      "required": [
                        "id",
                        "name"
                      ],
                      "additionalProperties": false
                    }
                  ]
                }
              },
              "required": [
                "gene",
                "elements"
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
