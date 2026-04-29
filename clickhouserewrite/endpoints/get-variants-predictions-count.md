# `GET /variants/predictions-count`

**Status:** 🚧 Mixed

**Router file:** [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts)

## Description

Retrieve counts of element gene predictions and cell types associated with a given variant.<br>   Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br>   spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941, ca_id = CA1522823495, files_fileset = ENCFF705MLV.

## OpenAPI excerpt

```json
{
  "operationId": "genomicElementsFromVariantsCount",
  "description": "Retrieve counts of element gene predictions and cell types associated with a given variant.<br>   Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br>   spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941, ca_id = CA1522823495, files_fileset = ENCFF705MLV.",
  "parameters": [
    {
      "name": "spdi",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "hgvs",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "ca_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "variant_id",
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
          "Mus musculus",
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
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
          "schema": {}
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
