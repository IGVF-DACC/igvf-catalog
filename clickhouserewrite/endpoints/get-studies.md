# `GET /studies`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/studies.ts`](../../src/routers/datatypeRouters/nodes/studies.ts)

## Description

Retrieve studies from GWAS. <br>   Example: study_id = GCST007798, <br>   pmid = 30929738. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "studies",
  "description": "Retrieve studies from GWAS. <br>   Example: study_id = GCST007798, <br>   pmid = 30929738. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "study_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "pmid",
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
                "name": {
                  "type": "string"
                },
                "ancestry_initial": {
                  "type": "string",
                  "nullable": true
                },
                "ancestry_replication": {
                  "type": "string",
                  "nullable": true
                },
                "n_cases": {
                  "type": "string",
                  "nullable": true
                },
                "n_initial": {
                  "type": "string",
                  "nullable": true
                },
                "n_replication": {
                  "type": "string",
                  "nullable": true
                },
                "pmid": {
                  "type": "string",
                  "nullable": true
                },
                "pub_author": {
                  "type": "string",
                  "nullable": true
                },
                "pub_date": {
                  "type": "string",
                  "nullable": true
                },
                "pub_journal": {
                  "type": "string",
                  "nullable": true
                },
                "pub_title": {
                  "type": "string",
                  "nullable": true
                },
                "has_sumstats": {
                  "type": "string",
                  "nullable": true
                },
                "num_assoc_loci": {
                  "type": "string",
                  "nullable": true
                },
                "study_source": {
                  "type": "string",
                  "nullable": true
                },
                "trait_reported": {
                  "type": "string",
                  "nullable": true
                },
                "trait_efos": {
                  "type": "string",
                  "nullable": true
                },
                "trait_category": {
                  "type": "string",
                  "nullable": true
                },
                "source": {
                  "type": "string"
                },
                "study_type": {
                  "type": "string",
                  "nullable": true
                },
                "version": {
                  "type": "string",
                  "nullable": true
                }
              },
              "required": [
                "_id",
                "name",
                "ancestry_initial",
                "ancestry_replication",
                "n_cases",
                "n_initial",
                "n_replication",
                "pmid",
                "pub_author",
                "pub_date",
                "pub_journal",
                "pub_title",
                "has_sumstats",
                "num_assoc_loci",
                "study_source",
                "trait_reported",
                "trait_efos",
                "trait_category",
                "study_type",
                "version"
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
