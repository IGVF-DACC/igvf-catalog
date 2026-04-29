# `GET /phenotypes/coding-variants`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts)

## Description

Retrieve coding variants associated with the query phenotype.<br>   Example: phenotype ID = OBA_0000128, <br>   phenotype_name = protein stability, <br>   files_fileset = IGVFFI2574RDFO, <br>   method = VAMP-seq, <br>   organism = Homo sapiens. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "codingVariantsFromPhenotypes",
  "description": "Retrieve coding variants associated with the query phenotype.<br>   Example: phenotype ID = OBA_0000128, <br>   phenotype_name = protein stability, <br>   files_fileset = IGVFFI2574RDFO, <br>   method = VAMP-seq, <br>   organism = Homo sapiens. <br>   The limit parameter controls the page size and can not exceed 100. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "phenotype_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "phenotype_name",
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
          "ESM-1v",
          "MutPred2",
          "SGE",
          "VAMP-seq"
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
                "coding_variant": {
                  "type": "object",
                  "properties": {
                    "_id": {
                      "type": "string"
                    },
                    "aapos": {
                      "type": "number",
                      "nullable": true
                    },
                    "hgvsp": {
                      "type": "string",
                      "nullable": true
                    },
                    "protein_name": {
                      "type": "string",
                      "nullable": true
                    },
                    "gene_name": {
                      "type": "string",
                      "nullable": true
                    },
                    "ref": {
                      "type": "string",
                      "nullable": true
                    },
                    "alt": {
                      "type": "string",
                      "nullable": true
                    }
                  },
                  "required": [
                    "_id"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                },
                "phenotype": {
                  "type": "object",
                  "properties": {
                    "phenotype_id": {
                      "type": "string"
                    },
                    "phenotype_name": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "phenotype_id",
                    "phenotype_name"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                },
                "score": {
                  "type": "number",
                  "nullable": true
                },
                "method": {
                  "type": "string",
                  "nullable": true
                },
                "class": {
                  "type": "string",
                  "nullable": true
                },
                "label": {
                  "type": "string",
                  "nullable": true
                },
                "files_filesets": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "variant": {
                  "type": "object",
                  "properties": {
                    "chr": {
                      "type": "string"
                    },
                    "pos": {
                      "type": "number"
                    },
                    "ref": {
                      "type": "string"
                    },
                    "alt": {
                      "type": "string"
                    },
                    "rsid": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "nullable": true
                    },
                    "spdi": {
                      "type": "string",
                      "nullable": true
                    },
                    "hgvs": {
                      "type": "string",
                      "nullable": true
                    },
                    "ca_id": {
                      "type": "string",
                      "nullable": true
                    },
                    "_id": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "chr",
                    "pos",
                    "ref",
                    "alt"
                  ],
                  "additionalProperties": false,
                  "nullable": true
                }
              },
              "required": [
                "score",
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
