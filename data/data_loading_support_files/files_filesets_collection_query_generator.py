def build_union_query(collections):
    parts = []
    for col in collections:
        block = f"""
        FOR doc IN {col}
          COLLECT files_fileset_id = doc.files_filesets WITH COUNT INTO count
          RETURN {{ files_fileset_id, collection: "{col}", count }}
        """
        parts.append(block.strip())
    union_query = 'RETURN UNION(' + \
        ', '.join(f'(\n{p}\n)' for p in parts) + ')'
    return union_query


collections = ['variants', 'coding_variants_phenotypes', 'genomic_elements', 'genomic_elements_genes', 'genomic_elements_biosamples',
               'variants_biosamples', 'variants_genomic_elements', 'variants_phenotypes_coding_variants', 'variants_phentoypes', 'variants_proteins', ' variants_genes']

print(build_union_query(collections))
print("Use the above query in: 'arangoexport --custom-query query.ql --type jsonl --server.database igvf --server.username igvf'")
