# `GET /genomic-elements`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/genomic_elements.ts`](../../src/routers/datatypeRouters/nodes/genomic_elements.ts)

## Description

Retrieve genomic elements.<br>   Example: region = chr1:1157520-1158189, <br>   source_annotation = dELS: distal Enhancer-like signal, <br>   type = candidate cis regulatory element, <br>   files_fileset = IGVFFI5749WPVK, <br>   source = ENCODE_SCREEN (ccREs). <br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "genomicElements",
  "description": "Retrieve genomic elements.<br>   Example: region = chr1:1157520-1158189, <br>   source_annotation = dELS: distal Enhancer-like signal, <br>   type = candidate cis regulatory element, <br>   files_fileset = IGVFFI5749WPVK, <br>   source = ENCODE_SCREEN (ccREs). <br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.",
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
      "name": "type",
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
          "MPRA",
          "Perturb-seq",
          "caQTL",
          "candidate Cis-Regulatory Elements",
          "integrative"
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
          "AFGR",
          "ENCODE",
          "FUNCODE",
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
          "Mus musculus",
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
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
    },
    {
      "name": "files_fileset",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
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
