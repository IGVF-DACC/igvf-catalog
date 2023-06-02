# Rules for Naming Catalog Nodes and Edges

1. Both node and edge collections are named according to the following formats:
    - lower case
    - use of underscores for spacing

2. Nodes:
    - Nodes are to be named according to their content in plural form.

    - Example: genes, proteins, transcripts, variants, ontological_terms, regulatory_regions


3. Edges:
    - Edges are to be named according to the parent-child relationship that they describe in singular form.

    - Example: variant_gene, gene_transcript, transcript_protein, ontological_term_ontological_term

- Transitive_closures are used only when biologically meaningful: such as for ontological relationships.
