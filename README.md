[![CircleCI](https://dl.circleci.com/status-badge/img/gh/IGVF-DACC/igvf-catalog/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/IGVF-DACC/igvf-catalog/tree/main)

# igvf-catalog
Catalog API repository for the IGVF project.

## Installing dependencies
1. Clone repository.
2. Install Python 3.11.
3. Install Node 18.13.0.
4. Install ArangoDB 3.10.0. (https://www.arangodb.com/docs/stable/installation.html)
5. Install JS dependencies: `npm install`
6. Install Python dependencies: `pip install -r data/requirements.txt`.

## Setting up your local database for the first time
You can either setup your local database or connect to our development database credentials. Please contact us for access. If you connect to our development database, you can skip this step.

For local setup:
1. Update `config/development.json` with your local ArangoDB credentials, with root access.
2. Execute the script: `cd data && python3 dev_setup.py`. This will load sample data of all datasets in the catalog into your local ArangoDB instance.

## Running locally
1. Make sure your `config/development.json` has your local ArangoDB credentials or our development cluster.
2. Run the server `npm run dev:server`.

The HTTP server with a Swagger interface displaying our endpoints will be available at: `http://localhost:2023`.
The TRPC interface is available at `http://localhost:2023/trpc`.

## Running tests
We use Jest for Typescript testing and Pytest for Python testing.
1. For typescript tests: `npm test`.
2. For python tests: `cd data && pytest`.

## Running with Docker Compose
1. Clone repository and make sure your Docker server is running.
2. Start services and load data:
```bash
$ docker compose up
$ docker compose up --build
```
3. An ArangoDB client should be available at `localhost:8529`. Default username and password are: `igvf`.

The HTTP server with a Swagger interface displaying our endpoints will be available at: `http://localhost:2023`.
The TRPC interface is available at `http://localhost:2023/trpc`.

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
Visit our beta Swagger page at:  https://api.catalog.igvf.org.

For any feature requests and bug reports please open a ticket at: https://github.com/IGVF-DACC/igvfd/issues.
