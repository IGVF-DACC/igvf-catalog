# Setting up endpoints in the Schema Config

Endpoints can automatically be configured in the `schema-config.yaml` file. This file is located in the `data` folder.

Three endpoints can be generated based on configurations of the model:

* Search (exact match) by a list of fields
* Fuzzy search by one given field
* Find by ID
* List parents or child nodes of a specific element
* Transitive Closure (all paths) from one node to another

Endpoints will be generated for each model if it contains the key `accessible_via` in its configuration.

## The `accessible_via` object

The `accessible_via` object defines ways to access objects of a certain model.

Assuming a gene object:

``` yaml
gene:
  represented_as: node
  label_in_input: gencode_gene
  db_collection_name: genes
  properties:
    chr: str
    start: str
    end: str
    gene_name: str
    gene_id: str
    gene_type: str

```

We can automatically set up endpoints to access *Genes* by adding the following block:

``` yaml
accessible_via:
  name: genes
  description: 'Retrieve gene information. Example: chr = chr1, gene_name = DDX11L1, gene_type = transcribed_unprocessed_pseudogene'
  filter_by: _id, chr, gene_name, gene_type
  filter_by_range: start, end
  fuzzy_text_search: gene_name
  return: _id, chr, gene_name, gene_type, start, end
```

The description of each field follows:

* `name`: defines the prefix of the endpoint name, in this example, all endpoints will start with `GET /genes/`.
* `description`: OpenAPI description of the endpoint. It will be consumed by OpenAPI clients such as Swagger.

* `filter_by`: a list of searchable properties that can be searched as query parameters. They define the "Filter by a list of fields" endpoint. All parameters must be defined in the `properties` object. Each field is optional, but **at least one field must be specified**. In this example, we can search a gene via: `GET /genes?chr=chr1&gene_name=ACT1&gene_type=pseudogene` for example. `_id` is the only exception as it's a reserved field and will not be read as a query parameter. If `_id` is set in this list, a separate endpoint "Find by ID" will be set, in this example: `GET /genes/{id}` will be created.
* `filter_by_range`: this list complements `filter_by` by specifying that `start` and `end` will define a range query. They can be used along with the other fields for searching. Currently, only `start` and `end` values are acceptable for this field.
* `fuzzy_text_search`: currently supporting only one field. This field will be searcheable returning objects that "fuzzy" match the value by using the Levenshtein metric. Search available via the endpoint `GET /genes/search/{term}`. The search indexes must be setup in order for this endpoint to work properly.
* `return`: the list of fields that will be returned by the endpoint. Each gene object will contain the fields: `_id, chr, gene_name, gene_type, start, end` in the response object.

So far, we discussed how to enable the endpoints: "Filter by a list of fields" (including range query) and "Find by ID". Now, let's discuss how to enable graph based endpoints automatically.

## Graph based endpoints

Graph based endpoints are automatically enabled depending on the relationships explicitly declared in edge models.

Here is one example on how to declare a relationship:

``` yaml
caqtl:
  represented_as: edge
  label_in_input: caqtl
  label_as_edge: VARIANT_OPEN_CHROMATIC_REGION
  db_collection_name: variant_open_chromatic_region_links
  db_collection_per_chromosome: false
  relationship:
    from: sequence variant
    to: open chromatin region
  properties:
    chr: str
    rsid: str
```

The `relationship` object can defined in any `edge` object and it must contain two keys: `from` and `to`.

The values of `from` and `to` must be a singular class name of a node also defined in the `schema-config.yaml` file.

In our example above, we are defining a relationship (sequence variant) -> (open chromatin region). This will automatically define the following endpoints, if the objects have an `accessible_via` object in their schema definitions:

* `GET /variants/{id}/children`
* `GET /chromatin-regions/{id}/parents`

which will return the list of children or parents nodes for a given ID respectively. And:

* `GET /caqtl/transitiveClosure/{from}/{to}`

which will return a list of all directional paths starting from the node ID: `from` and which ends in the node ID: `to`.
