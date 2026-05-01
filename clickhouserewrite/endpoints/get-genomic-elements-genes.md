# `GET /genomic-elements/genes`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/genomic_elements_genes.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_genes.ts)

## Description

Retrieve genomic elements and gene pairs by querying genomic elements.<br>   One of those fields is required: region, method, files_fileset. <br>   Example region = chr1:903900-904900. <br>   source_annotation = enhancer. <br>   region_type = accessible dna elements; <br>   method = CRISPR FACS screen. <br>   files_fileset = ENCFF968BZL. <br>   biosample_term = EFO_0002067. <br>   biological_context = placenta from ENCDO091OEF. <br>   source = ENCODE, <br>   Set verbose = true to retrieve full info on the genes, genomic element.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genesFromGenomicElements",
  "description": "Retrieve genomic elements and gene pairs by querying genomic elements.<br>   One of those fields is required: region, method, files_fileset. <br>   Example region = chr1:903900-904900. <br>   source_annotation = enhancer. <br>   region_type = accessible dna elements; <br>   method = CRISPR FACS screen. <br>   files_fileset = ENCFF968BZL. <br>   biosample_term = EFO_0002067. <br>   biological_context = placenta from ENCDO091OEF. <br>   source = ENCODE, <br>   Set verbose = true to retrieve full info on the genes, genomic element.<br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
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
      "name": "source_annotation",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "CA-CTCF: chromatin accessible + CTCF binding",
          "CA-H3K4me3: chromatin accessible + H3K4me3 high signal",
          "CA-TF: chromatin accessible + TF binding",
          "CA: chromatin accessible",
          "PLS: Promoter-like signal",
          "TF: TF binding",
          "dELS: distal Enhancer-like signal",
          "enhancer",
          "genic",
          "intergenic",
          "negative control",
          "pELS: proximal Enhancer-like signal",
          "promoter"
        ]
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
                "crispr_modality": {
                  "type": "string",
                  "nullable": true
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
