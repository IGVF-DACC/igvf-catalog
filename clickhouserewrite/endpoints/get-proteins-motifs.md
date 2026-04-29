# `GET /proteins/motifs`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/motifs_proteins.ts`](../../src/routers/datatypeRouters/edges/motifs_proteins.ts)

## Description

Retrieve motifs for proteins.<br>   Set verbose = true to retrieve full info on the motifs.<br>   Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br>   protein_name = CTCF, <br>   uniprot_name = CTCF_HUMAN, <br>   uniprot_full_name = Transcriptional repressor CTCF, <br>   dbxrefs = P49711,<br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "motifsFromProteins",
  "description": "Retrieve motifs for proteins.<br>   Set verbose = true to retrieve full info on the motifs.<br>   Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br>   protein_name = CTCF, <br>   uniprot_name = CTCF_HUMAN, <br>   uniprot_full_name = Transcriptional repressor CTCF, <br>   dbxrefs = P49711,<br>   The limit parameter controls the page size and can not exceed 1000. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "protein_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "protein_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "uniprot_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "uniprot_full_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "dbxrefs",
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
                "protein": {
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
                  ]
                },
                "complex": {
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
                        "alias": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "molecules": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "nullable": true
                        },
                        "evidence_code": {
                          "type": "string",
                          "nullable": true
                        },
                        "experimental_evidence": {
                          "type": "string",
                          "nullable": true
                        },
                        "description": {
                          "type": "string",
                          "nullable": true
                        },
                        "complex_assembly": {
                          "anyOf": [
                            {
                              "type": "string"
                            },
                            {
                              "type": "array",
                              "items": {
                                "type": "string"
                              }
                            }
                          ],
                          "nullable": true
                        },
                        "complex_source": {
                          "type": "string",
                          "nullable": true
                        },
                        "reactome_xref": {
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
                "motif": {
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
                        "tf_name": {
                          "type": "string"
                        },
                        "length": {
                          "type": "number"
                        },
                        "pwm": {
                          "type": "array",
                          "items": {
                            "type": "array",
                            "items": {
                              "anyOf": [
                                {
                                  "not": {}
                                },
                                {
                                  "type": "string"
                                }
                              ]
                            }
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
                        "name",
                        "tf_name",
                        "length",
                        "pwm",
                        "source",
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
