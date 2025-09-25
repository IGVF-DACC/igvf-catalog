
# igvf-catalog

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/IGVF-DACC/igvf-catalog/tree/dev.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/IGVF-DACC/igvf-catalog/tree/dev)
[![Coverage Status](https://coveralls.io/repos/github/IGVF-DACC/igvf-catalog/badge.svg?branch=dev&kill_cache=1)](https://coveralls.io/github/IGVF-DACC/igvf-catalog?branch=dev)

Catalog API repository for the IGVF project.

## Running with Docker Compose

Clone repository and make sure your Docker server is running.

### When running for the first time, or if you want to load new data

Make sure `data/parsed_data` is empty, otherwise duplicates might be created.
Load data and initialize the database:

```bash
docker compose -f docker-compose-loader.yml up --build
```

After the python container exits either hit ctrl+C or run:

```bash
docker compose -f docker-compose-loader.yml down
```

### When data has been loaded and you want to start the services

Run:

```bash
docker compose -f docker-compose-serve.yml up
```

An ArangoDB client should be available at `localhost:8529`. Default username and password are: `igvf`.

The HTTP server with a Swagger interface displaying our endpoints will be available at: `http://localhost:2023`.
The TRPC interface is available at `http://localhost:2023/trpc`.

### Running with a remote Arango instance

In `docker-compose-serve.yml` define the environment variables `IGVF_CATALOG_ARANGODB_URI`, `IGVF_CATALOG_ARANGODB_USERNAME` and `IGVF_CATALOG_ARANGODB_PASSWORD` with appropriate values, and that database will be used as the backend instead of the one running in docker locally.

## Running tests

We use Jest for Typescript testing and Pytest for Python testing. For running tests, inside of the docker container:

1. For typescript tests: `npm test`.
2. For python tests: `cd data && pytest`.

If running tests outside of the docker container, you will need to install the project dependencies:

1. `npm install`
2. `cd data && pip install -r requirements.txt` (we suggest the use of a virtual environment to manage your Python packages)

## Using the TRPC server in a Typescript project

If your project is in Typescript, you can execute remote procedure calls (RPCs) by importing this repository into your project and calling available procedures. The example below shows how to fetch gene data using tRPC.

```typescript
import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './routers/_app'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023/trpc' })
    ]
  })

  // tRPC call to fetch gene data
  const gene = await trpc.genes.query({
    gene_id: 'ENSG00000160336'
  })

  console.log(gene)
}

void main()
```

The object `trpc` in this example can be inspected for a full list of all available remote procedures available. The full list is the same available at `http://localhost:2023/`.

## Automatic linting

This repo includes configuration for pre-commit hooks. To use pre-commit, install pre-commit, and activate the hooks:

```bash
pip install pre-commit==3.2.1
pre-commit install
```

## Live demo

Visit our beta Swagger page at:  <https://api.catalog.igvf.org>.

For any feature requests and bug reports please open a ticket at: <https://github.com/IGVF-DACC/igvfd/issues>.
