[![CircleCI](https://dl.circleci.com/status-badge/img/gh/IGVF-DACC/igvf-catalog/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/IGVF-DACC/igvf-catalog/tree/main)

# igvf-catalog
Catalog API repository for the IGVF project

## Run with Docker Compose
1. Clone repository and make sure Docker is running.
2. Start services and load data inserts:
```bash
# From repository.
$ docker compose up
# Note if any dependencies have changed (e.g. switching between branches that
# rely on different versions of snovault) use the build flag as well
# to rebuild the underlying Docker image:
$ docker compose up --build
```
3. Browse at `localhost:2023`.
4. ArangoDB Client is available at `localhost:8529`. Default username and password are `igvf`.

## Running locally
1. Clone repository.
2. Install Python 3.11.
3. Install Node 18.13.0.
4. Install ArangoDB 3.10.0. (https://www.arangodb.com/docs/stable/installation.html)
5. Install JS dependencies: `npm install`
6. Install Python dependencies: `pip install -r data/requirements.txt`. It's recommended to have a tool to create an isolated Python environment, such as virtualenv.
7. Update `config/development.json` with your ArangoDB root credentials.
8. Load sample data with `cd data && python3 dev_setup.py`.
9. Run tests: `npm test` and `cd data && pytest`.
10. Run the server `npm run dev:server`.
11. Server should be available at: `localhost:2023` for Swagger interface, and `localhost:2023/trpc` for tRPC interface.

## Automatic linting

This repo includes configuration for pre-commit hooks. To use pre-commit, install pre-commit, and activate the hooks:

```bash
pip install pre-commit==3.2.1
pre-commit install
```

## Live demo

This project is currently in an early stage (alpha version) of development.

The steps described above are deployed and available at: https://api.catalog.igvf.org. The data available via our current API comes from our alpha database catalog.

The live demo is a public work in progress where we share our progress and make discussions available. It is not ready for any usage in any production-level application yet.
