# Rules for Naming Catalog Nodes and Edges

1. Both node and edge collections are named according to the following formats:
    - lower case
    - use of underscores for spacing
    - plural form

2. Nodes
Nodes are to be named according to their content in plural form.
For example: genes, proteins, transcripts, variants, ontological_terms, regulatory_regions


## Edge Collections
Edges are to be named according to the parent-child relationship that they contain in singular form.

Example: ontological_term_ontologocal_term or variant_gene

- Transitive_closure is applicable only for ontological_term relationships.


#### Motifs - tbd.


## API Functions

API functions querying edge collections (parents/children) should be named depending on the entities and directionality. Different edges require different names for the same query function.

For example: Looking at the variant_gene edge to be able to find:
* all variants (parents) for a given gene (child):
* all genes (children) for a given variant (parent):
