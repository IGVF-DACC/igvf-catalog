AQL_EXAMPLES = """
    # Tell me about gene SAMD11
    FOR gene IN genes
    FILTER gene.name == "SAMD11"
    RETURN gene

    # show me all the vairants that is in chromosome 1, position at 10000000?
    WITH variants
    FOR v IN variants
    FILTER v.chr == "chr1" AND v.pos == 10000000
    RETURN v

    # Can you tell me the variant with SPDI of NC_000012.12:102855312:C:T is associated with what diseases?
    WITH variants, variants_diseases, ontology_terms
    FOR variant IN variants
    FILTER variant.spdi == 'NC_000012.12:102855312:C:T'
    FOR disease IN OUTBOUND variant variants_diseases
    RETURN disease

    # Show me all variants associated with cardiomyopathy
    FOR v in variants
    FILTER v._id IN (
        FOR d IN variants_diseases
        FILTER d._to IN (
        FOR o in ontology_terms
        FILTER o.name == 'cardiomyopathy'
        RETURN o._id
        )
    RETURN d._from)
    RETURN v

    # What are the transcripts from the protein PARI_HUMAN?
    FOR p IN proteins
        FILTER 'PARI_HUMAN' in p.names
        FOR t IN transcripts_proteins
            FILTER t._to == p._id
            RETURN DOCUMENT(t._from)

    # what genomic elements overlap rs1047055?
    LET variant = FIRST(
    FOR v IN variants
        FILTER "rs1047055" in v.rsid
        RETURN { chr: v.chr, pos: v.pos}
    )
    FOR g IN genomic_elements OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }
        FILTER g.chr == variant.chr AND g.start <= variant.pos AND g.end > variant.pos
        RETURN DISTINCT g

    # For eQTL data, what variants are active in tissue that is part of heart.
    LET heartTerms = (
    FOR t IN ontology_terms
        FILTER t.name == "heart"
        FOR v, e IN 1..7 INBOUND t ontology_terms_ontology_terms
            FILTER e.name IN ["part of"]
            RETURN DISTINCT v
    )
    FOR tgt IN heartTerms
        FOR vgt IN variants_genes_terms
            FILTER vgt._to == tgt._id
            FOR vg IN variants_genes
                FILTER vg._id == vgt._from AND vg.label == "eQTL"
                limit 5
                RETURN DISTINCT { term: tgt, variant: vg._from, gene: DOCUMENT(vg._to)}

    # Find the genomic elements that are linked to PP1F (ENSG0000ENSG00000187642), with score >0.85
    WITH genomic_elements, genomic_elements_genes
    FOR gene IN genomic_elements_genes
        FILTER gene._to == "genes/ENSG00000187642" AND gene.score > 0.85
        FOR element IN genomic_elements
            FILTER element._id == gene._from
            RETURN element

    # Find the top 5 eQTLs in ontology term named amygdala, sorted by p_value.
    LET heartTerms = (
    FOR t IN ontology_terms
        FILTER t.name == "amygdala"
        RETURN t
    )
    FOR vgt IN variants_genes_terms
        FILTER vgt._to in heartTerms[*]._id
    FOR vg in variants_genes
        FILTER vgt._from == vg._id AND vg.label == "eQTL"
        SORT vg.`p_value` ASC
        LIMIT 5
        LET gene = DOCUMENT(vg._to)
        LET variant = DOCUMENT(vg._from)
    RETURN {'p-val': vg.`p_value`,
            'biosample': vg.biological_context,
            'gene': gene.name,
            'variant': variant.spdi}

    # For variant with rsID rs309428, find the genomic elements that it is contained in.
    LET variant = FIRST(
        FOR v IN variants
            FILTER "rs309428" in v.rsid
            RETURN v
    )
    FOR g IN genomic_elements OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }
        FILTER g.chr == variant.chr AND g.start <= variant.pos AND g.end > variant.pos
        RETURN g

    # Find the top 5 genes that are co-expressed with gene ENSG00000261221, sorted by z_score.
    FOR gg in genes_genes
        FILTER gg._from == 'genes/ENSG00000261221'
        SORT gg.`z_score` ASC
        limit 5
        RETURN gg

    # Find genes that are linked to variant with SPDI NC_000005.10:173860847:G:A.
    LET variant = FIRST(
        FOR v IN variants
            FILTER v.spdi == 'NC_000005.10:173860847:G:A'
            RETURN v
    )
    FOR vg IN variants_genes
        FILTER vg._from == variant._id
        FOR gene IN genes
            FILTER gene._id == vg._to
            RETURN distinct gene

    # Is variant with rsID rs875741 a caQTL?
    FOR v in variants
        FILTER "rs875741" in v.rsid
    FOR vg IN variants_genomic_elements
        FILTER vg._from == v._id
        return vg

    # find 5 variants linked to gene ENSG00000188290.
    FOR vg IN variants_genes
        FILTER vg._to == 'genes/ENSG00000188290'
        LIMIT 5
        FOR v IN variants
            FILTER v._id == vg._from
            RETURN v

    # What diseases are associated with variant with gene PAH?
    FOR gene IN genes
    FILTER gene.name == "PAH"
    FOR edge IN diseases_genes
        FILTER edge._to == gene._id
        FOR disease IN ontology_terms
        FILTER disease._id == edge._from
        RETURN disease
    """
