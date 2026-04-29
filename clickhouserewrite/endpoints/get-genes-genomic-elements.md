# `GET /genes/genomic-elements`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/genomic_elements_genes.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_genes.ts)

## Description

Retrieve genomic elements and gene pairs by querying genes.<br>   One of those fields is required: gene_id, hgnc_id, gene_name, alias, method, files_fileset. <br>   Example: gene_id = ENSG00000187961, <br>   gene_name = SARS1, <br>   hgnc = HGNC:10537, <br>   alias = SERRS, <br>   method = Pertub-seq, <br>   files_fileset = IGVFFI3069QCRA. <br>   biosample_term = EFO_0002067. <br>   biological_context = placenta from ENCDO091OEF. <br>   source = IGVF. <br>   Set verbose = true to retrieve full info on the genes, genomic element.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genomicElementsFromGenes",
  "description": "Retrieve genomic elements and gene pairs by querying genes.<br>   One of those fields is required: gene_id, hgnc_id, gene_name, alias, method, files_fileset. <br>   Example: gene_id = ENSG00000187961, <br>   gene_name = SARS1, <br>   hgnc = HGNC:10537, <br>   alias = SERRS, <br>   method = Pertub-seq, <br>   files_fileset = IGVFFI3069QCRA. <br>   biosample_term = EFO_0002067. <br>   biological_context = placenta from ENCDO091OEF. <br>   source = IGVF. <br>   Set verbose = true to retrieve full info on the genes, genomic element.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
          "CRISPR FACS screen",
          "CRISPR enhancer perturbation screen",
          "ENCODE-rE2G",
          "Perturb-seq",
          "TAP-seq"
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
                "name": {
                  "type": "string"
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
                "biological_context": {
                  "type": "string"
                },
                "biosample_term": {
                  "type": "string"
                },
                "files_filesets": {
                  "type": "string"
                },
                "score": {
                  "type": "number",
                  "nullable": true
                },
                "p_value": {
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
                        "type": {
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
                        "name": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "_id",
                        "name"
                      ],
                      "additionalProperties": false
                    }
                  ]
                },
                "gene": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
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
                    }
                  ]
                }
              },
              "required": [
                "name",
                "label",
                "method",
                "class",
                "source",
                "source_url",
                "biological_context",
                "biosample_term",
                "files_filesets",
                "score",
                "genomic_element",
                "gene"
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
