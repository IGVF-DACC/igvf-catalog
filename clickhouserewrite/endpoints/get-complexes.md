# `GET /complexes`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/complexes.ts`](../../src/routers/datatypeRouters/nodes/complexes.ts)

## Description

Retrieve complexes.<br>   Example: complex_id = CPX-11, <br>   name = SMAD2, <br>   description = phosphorylation. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "complexes",
  "description": "Retrieve complexes.<br>   Example: complex_id = CPX-11, <br>   name = SMAD2, <br>   description = phosphorylation. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "complex_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "description",
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
            "anyOf": [
              {
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
