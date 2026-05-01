# `GET /files-filesets`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/files_filesets.ts`](../../src/routers/datatypeRouters/nodes/files_filesets.ts)

## Description

Retrieve data about a specific dataset.<br>   Example: file_fileset_id = ENCFF004PFU,<br>  fileset_id = ENCSR359DFW,<br>  lab = jesse-engreitz,<br>  preferred_assay_title = DNase-seq,<br>  method = MPRA,<br>  donor_id = ENCDO000AAK,<br>  sample_term = EFO_0002784,<br>  sample_summary = GM12878,<br>  software = Distal regulation ENCODE-rE2G,<br>  class = prediction,<br>  source = ENCODE.<br>  The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "filesFilesets",
  "description": "Retrieve data about a specific dataset.<br>   Example: file_fileset_id = ENCFF004PFU,<br>  fileset_id = ENCSR359DFW,<br>  lab = jesse-engreitz,<br>  preferred_assay_title = DNase-seq,<br>  method = MPRA,<br>  donor_id = ENCDO000AAK,<br>  sample_term = EFO_0002784,<br>  sample_summary = GM12878,<br>  software = Distal regulation ENCODE-rE2G,<br>  class = prediction,<br>  source = ENCODE.<br>  The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "file_fileset_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "fileset_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "lab",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "alan-boyle",
          "bill-majoros",
          "charles-gersbach",
          "doug-fowler",
          "j-michael-cherry",
          "jay-shendure",
          "jesse-engreitz",
          "karen-mohlke",
          "kushal-dey",
          "lea-starita",
          "mark-craven",
          "nadav-ahituv",
          "predrag-radivojac",
          "thomas-quertermous",
          "tim-reddy",
          "zhiping-weng"
        ]
      }
    },
    {
      "name": "preferred_assay_title",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "CRISPR FACS screen",
          "DNase-seq",
          "MPRA",
          "Perturb-seq",
          "SGE",
          "STARR-seq",
          "TAP-seq",
          "VAMP-seq",
          "VAMP-seq (MultiSTEP)",
          "Variant-EFFECTS",
          "electroporated MPRA",
          "lentiMPRA",
          "scATAC-seq"
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
          "BlueSTARR",
          "CRISPR screen",
          "ENCODE-rE2G",
          "ESM-1v",
          "Homo sapiens elements",
          "MPRA",
          "MutPred2",
          "Perturb-seq",
          "SEMVAR",
          "SGE",
          "STARR-seq",
          "TAP-seq",
          "VAMP-seq",
          "VAMP-seq (MultiSTEP)",
          "Variant-EFFECTS",
          "cV2F",
          "caQTL",
          "candidate Cis-Regulatory Elements",
          "elements",
          "scATAC-seq"
        ]
      }
    },
    {
      "name": "crispr_modality",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "activation",
          "interference",
          "knockout",
          "prime editing"
        ]
      }
    },
    {
      "name": "donor_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "sample_term",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "sample_summary",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "software",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "2024_multistep",
          "BCalm",
          "BEDTools",
          "BIRD",
          "BlueSTARR",
          "CountESS",
          "DESeq2",
          "Distal regulation ENCODE-rE2G",
          "DistalRegulationCRISPRdata",
          "ESM-1v",
          "Engreitz Variant-EFFECTS scripts",
          "FRACTEL",
          "MPRAflow tsv-to-bed",
          "MutPred2",
          "SEMVAR",
          "SGE Pipeline",
          "Samtools",
          "Sceptre",
          "Seurat",
          "bigWigAverageOverBed",
          "cV2F",
          "cyp2c19_2c9",
          "mpralm",
          "pandas",
          "scATAC-seq processing scripts"
        ]
      }
    },
    {
      "name": "cell_annotation",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "extraembryonic parietal endodermal cell",
          "extraembryonic visceral endodermal cell",
          "intermediate extraembryonic parietal endodermal cell",
          "mesodermal cell",
          "neurectodermal cell",
          "pluripotent epiblast cell",
          "surface ectodermal cell"
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
      "name": "class",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "biological relationship",
          "observed data",
          "prediction"
        ]
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
                "_id": {
                  "type": "string"
                },
                "file_set_id": {
                  "type": "string"
                },
                "lab": {
                  "type": "string"
                },
                "preferred_assay_titles": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "assay_term_ids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "method": {
                  "type": "string"
                },
                "class": {
                  "type": "string"
                },
                "software": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "collections": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "samples": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "sample_ids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "simple_sample_summaries": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "nullable": true
                },
                "donors": {
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
                },
                "download_link": {
                  "type": "string"
                },
                "cell_annotation": {
                  "type": "string",
                  "nullable": true
                },
                "genome_browser_link": {
                  "type": "string",
                  "nullable": true
                },
                "crispr_modality": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "file_set_id",
                "lab",
                "method",
                "class",
                "source",
                "source_url",
                "download_link"
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
