AQL_EXAMPLES = """
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
        FILTER p.name == 'PARI_HUMAN'
        FOR t IN transcripts_proteins
            FILTER t._to == p._id
            RETURN t
    """
