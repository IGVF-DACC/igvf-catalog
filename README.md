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
