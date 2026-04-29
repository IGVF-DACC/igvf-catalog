# `GET /motifs`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/nodes/motifs.ts`](../../src/routers/datatypeRouters/nodes/motifs.ts)

## Description

Retrieve transcription factor binding motifs from HOCOMOCO.<br>   Example: tf_name = STAT3_HUMAN, <br>   source = HOCOMOCOv11. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "motifs",
  "description": "Retrieve transcription factor binding motifs from HOCOMOCO.<br>   Example: tf_name = STAT3_HUMAN, <br>   source = HOCOMOCOv11. <br>   The limit parameter controls the page size and can not exceed 500. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "tf_name",
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
          "IGVF",
          "HOCOMOCOv11"
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
