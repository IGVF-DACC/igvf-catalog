# Loading data into the IGVF Catalog

The current architecture of the IGVF Catalog contains two databases: ArangoDB (a graph database) and ClickhouseDB (a columnar database).

Each database is optimized for specific operations that implement use cases of the IGVF Catalog. Both databases are loaded with the same data provided by a list of datasets.

Each dataset is listed in the Data Sources file at `igvf-catalog/data/data_sources.yaml`.

The Data Sources file lists all datafile links needed to load a dataset into the Catalog. It also describes how to parse each input file. For example:

```
# Example: pypy3 data_parser.py --adapter topld --output-bucket igvf-catalog-parsed-collections --filepath ~/topld/afr/AFR_chr1_no_filter_0.2_1000000_LD.csv --output-bucket-key variants_variants/topld_afr_chr1.jsonl --chr chr1 --annotation-filepath ~/topld/afr/AFR_chr1_no_filter_0.2_1000000_info_annotation.csv --ancestry AFR
topld in linkage disequilibrium with:
  collection: variants_variants
  params:
    - chr
    - annotation-filepath
    - ancestry
  command: pypy3 data_parser.py --adapter topld --output-bucket igvf-catalog-parsed-collections --filepath {datafile} --output-bucket-key {collection}/topld_{ancestry}_{chr}.jsonl --chr {chr} --annotation-filepath {annotation_datafile} --ancestry {ancestry}
  pypy3: true
  datafiles:
    - AFR:
      - chr1:
        - https://api.data.igvf.org/reference-files/IGVFFI4988BAVR/@@download/IGVFFI4988BAVR.csv.gz # AFR_chr1_no_filter_0.2_1000000_info_annotation.csv.gz
        - https://api.data.igvf.org/reference-files/IGVFFI6426PMAM/@@download/IGVFFI6426PMAM.csv.gz # AFR_chr1_no_filter_0.2_1000000_LD.csv.gz
      - chr2:
        - https://api.data.igvf.org/reference-files/IGVFFI0965IFWW/@@download/IGVFFI0965IFWW.csv.gz # AFR_chr2_no_filter_0.2_1000000_info_annotation.csv.gz
        - https://api.data.igvf.org/reference-files/IGVFFI0049LYPQ/@@download/IGVFFI0049LYPQ.csv.gz # AFR_chr2_no_filter_0.2_1000000_LD.csv.gz
      ...
    ...
...
```

This excerpt of the original `data_sources.yaml` lists an incomplete set of 4 files from the TopLD dataset that are part of the `variants_variants` collection/table.

For this specific case, each chromosome for each ancestry requires a data file and an annotation data file. The template of the parameters necessary to run the parser is indicated in the file and an example is given on top of each group:

```
pypy3 data_parser.py --adapter topld --output-bucket igvf-catalog-parsed-collections --filepath ~/topld/afr/AFR_chr1_no_filter_0.2_1000000_LD.csv --output-bucket-key variants_variants/topld_afr_chr1.jsonl --chr chr1 --annotation-filepath ~/topld/afr/AFR_chr1_no_filter_0.2_1000000_info_annotation.csv --ancestry AFR
```

In this case, we use the adapter `topld` for loading the datafile `AFR_chr1_no_filter_0.2_1000000_LD.csv` with annotation file `AFR_chr1_no_filter_0.2_1000000_info_annotation.csv`, for the chromosome `chr1`, and ancestry `AFR`. This same template must be applied to all the other files in the list to complete the `variants_variants` collection.

Each data file must be downloaded from the IGVF Data Portal (https://data.igvf.org).

Each adapter requires its own set of individual parameters which are also listed for each block. However, all adapters will require a `--filepath` parameter.

Certain adapters are compatible with `pypy3` which can speed up its execution by a substantial amount of time.

All examples are written expecting the storage of each JSON directly into S3. To write the JSONL in a local folder, use the `--output-local-path` parameter by passing the local path. For example `--output-local-path ~/jsonls/variants_variants/topld_afr_chr1.jsonl`.

For this example, the output JSONL will be written in the S3 bucket `igvf-catalog-parsed-collections` in the `variants_variants/topld_afr_chr1.jsonl`. Both S3 bucket and S3 key value must be specified. The instance running this script must have permission to write into this particular S3 bucket. The AWS profile can be customized with the `--aws-profile` parameter, for example `--aws-profile igvf-dev`, if necessary.

All JSONLs are grouped by folders representing each collection/table in the databases. Each folder contains all data necessary, which can be loaded into ArangoDB and Clickhouse.

## Loading data into ArangoDB

There are two ways to import data into ArangoDB: manually or by using an automated script (`data_ingestion.py`).

Before importing any data, create all necessary collections (nodes and/or edges) using the ArangoDB web interface. Large collections such as `variants`, `variants_variants`, `coding_variants`, etc must be sharded. Also, depending on the free space in the data nodes in the cluster, collections must be transferred to appropriated data nodes before having data lodaded. Transferring loaded collections between data nodes later on is susceptible to data corruption, especially if collections are very large.

### Manually

Any JSONL file can be imported into ArangoDB by using the tool `arangoimport` (https://docs.arangodb.com/stable/components/tools/arangoimport/details/).

For example, importing the local file `example.jsonl` into the `example-collection` collection can be done by the following command:

`arangoimport --file example.jsonl --collection example-collection --server.database igvf --server.username username --server.password password --on-duplicate replace`

The server credentials can be passed as arguments of the command or defined separately in a local file named `arangoimp.conf` which can be located at the current path or at `~/.arangodb/arangoimp.conf` with the following format:

```
server.database = igvf
server.username = username
server.password = password
server.authentication = true
```

It's recommended to execute `arangoimport` from within any of the data nodes of the cluster to save network latency time especially when the JSONLs are large.

The `--on-duplicate` parameter plays an important role in loading a few datasets. For example, for the `variants` collection, we first load the original FAVOR dataset, then replace existing variants with updated variants from the y2ave JSONL and finally, we add autogenerated variants from the DBSNFP dataset if they do not exist in the FAVOR dataset. This logic is implemented using the `--on-duplicate` parameter:

1) `arangoimport --file favor-chr*.jsonl --collection variants`
2) `arangoimport --file y2ave.jsonl --collection variants --on-duplicate replace`
3) `arangoimport --file autogenerated.jsonl --collection variants --on-duplicate ignore`

The `variants` collection is the only collection that requires manual loading because of this particular logic. All other collections can be loaded using the automated script.

### Automated Script

The script `data_ingestion.py` automatically imports JSONL files into ArangoDB. Files can be local or the script can automatically download all necessary JSONLs from   S3.

The ArangoDB connection credentials used by the script are the ones defined in the `igvf-catalog/config/development.json` file.

#### Importing a local file

For example, in order to load the collection `genes` using the local file `gencode.jsonl`:

`python3 data_ingestion.py --collection genes --file gencode.jsonl`

Alternatively, you can use a dry-run method to output the `arangoimport` command via:

`python3 data_ingestion.py --collection genes --file gencode.jsonl --dry-run`

#### Importing files from S3

The script can automatically download all necessary files to load a collection from S3.

Following the example above, in order to load the `genes` collection from the JSONLs stored in S3, just run:

`python3 data_ingestion.py --collection genes --s3`

It will automatically pull files from the `s3://igvf-catalog-parsed-collections` bucket. If you wish to use a different bucket you can set the parameter `--s3-bucket`.

After loading each JSONL file, the script will delete each file to save space (certain datasets are very large). If you wish to keep the files in your local storage, use the flag `--keep-files`.


## Loading data into ClickhouseDB

ClickhouseDB has the native support to download and import files from within its client.

Before loading data, it's necessary to create each table and load its schema.

All schemas are defined in: `igvf-catalog/data/db/schema/clickhouse_schema.sql`. The whole file can be executed in the Clickhouse client: `$ clickhouse-client --user default --password <password>`.

You can also connect to the server using third-party clients such as DBVisualizer.

We currently support manually importing into ClickhouseDB only. Automated support is under development.

For each collection, all `INSERT` commands are listed in the `igvf-catalog/data/db/schema/clickhouse_import.yaml` file.

For example, to load the table `genes`, execute the series of commands under the key `genes` in the `clickhouse_import.yaml` file:

```
genes: |
  INSERT INTO genes
  SELECT chr, start, end, name, gene_id, gene_type, hgnc, entrez, alias, source, version, source_url, 'Homo sapiens', _key as id
  FROM s3('s3://igvf-catalog-parsed-collections/genes/genes_*.jsonl');
```

Clickhouse automatically downloads all JSONL files that accept the `genes/genes_*.jsonl` pattern and imports them into the table `genes`.
