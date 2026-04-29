# `GET /transcripts/proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/transcripts_proteins.ts`](../../src/routers/datatypeRouters/edges/transcripts_proteins.ts)

## Description

Retrieve proteins from transcripts.<br>     Set verbose = true to retrieve full info on the proteins.<br>     Example: region = chr16:67562500-67640000, <br>     transcript_type = protein_coding, <br>     transcript_id = ENST00000401394 (Ensembl ID). <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "proteinsFromTranscripts",
  "description": "Retrieve proteins from transcripts.<br>     Set verbose = true to retrieve full info on the proteins.<br>     Example: region = chr16:67562500-67640000, <br>     transcript_type = protein_coding, <br>     transcript_id = ENST00000401394 (Ensembl ID). <br>     The limit parameter controls the page size and can not exceed 100. <br>     Pagination is 0-based.",
  "parameters": [
    {
      "name": "transcript_id",
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
      "name": "transcript_type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "IG_C_gene",
          "IG_C_pseudogene",
          "IG_D_gene",
          "IG_J_gene",
          "IG_J_pseudogene",
          "IG_V_gene",
          "IG_V_pseudogene",
          "IG_pseudogene",
          "Mt_rRNA",
          "Mt_tRNA",
          "TEC",
          "TR_C_gene",
          "TR_D_gene",
          "TR_J_gene",
          "TR_J_pseudogene",
          "TR_V_gene",
          "TR_V_pseudogene",
          "artifact",
          "lncRNA",
          "miRNA",
          "misc_RNA",
          "non_stop_decay",
          "nonsense_mediated_decay",
          "processed_pseudogene",
          "processed_transcript",
          "protein_coding",
          "protein_coding_CDS_not_defined",
          "protein_coding_LoF",
          "pseudogene",
          "rRNA",
          "rRNA_pseudogene",
          "retained_intron",
          "ribozyme",
          "sRNA",
          "scRNA",
          "scaRNA",
          "snRNA",
          "snoRNA",
          "transcribed_processed_pseudogene",
          "transcribed_unitary_pseudogene",
          "transcribed_unprocessed_pseudogene",
          "translated_processed_pseudogene",
          "translated_unprocessed_pseudogene",
          "unitary_pseudogene",
          "unprocessed_pseudogene",
          "vault_RNA"
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
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "protein": {
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
                          "dbxrefs": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "properties": {
                                "name": {
                                  "type": "string"
                                },
                                "id": {
                                  "type": "string"
                                }
                              },
                              "required": [
                                "name",
                                "id"
                              ],
                              "additionalProperties": false
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
                    }
                  ]
                },
                "transcript": {
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
                        "transcript_type": {
                          "type": "string"
                        },
                        "chr": {
                          "type": "string"
                        },
                        "start": {
                          "type": "number"
                        },
                        "end": {
                          "type": "number"
                        },
                        "strand": {
                          "type": "string"
                        },
                        "name": {
                          "type": "string"
                        },
                        "gene_name": {
                          "type": "string"
                        },
                        "MANE_Select": {
                          "type": "boolean",
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
                        "transcript_type",
                        "chr",
                        "start",
                        "end",
                        "strand",
                        "name",
                        "gene_name",
                        "source",
                        "version",
                        "source_url"
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
