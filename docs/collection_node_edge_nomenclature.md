# Rules for Naming Catalog Nodes and Edges

1. Both node and edge collections are named according to the following formats:
    - lower case
    - use of underscores for spacing

2. Nodes:
    - Nodes are to be named according to their content in plural form.

    - Example: genes, proteins, transcripts, variants, ontological_terms, regulatory_regions


3. Edges:
    - Edges are to be named according to the parent-child relationship that they describe in plural form.
    - If the edge is directional, put the parent first, e.g,. genes_transcripts

    - Example: variants_genes, genes_transcripts, transcripts_proteins, ontological_terms_ontological_terms

- Transitive_closures are used only when biologically meaningful: such as for ontological relationships.
