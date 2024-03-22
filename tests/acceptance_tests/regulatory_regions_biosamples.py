regulatory_regions_biosamples = {
    '/regulatory_regions/biosamples': [{
        'params': {
            'type': 'MPRA_expression_tested',
            'region': 'chr10:100038743-100038963',
            'verbose': 'false'
        },
        'response': [
            {
                'activity_score': 0.226,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF475FKV/',
                'ontology term': 'ontology_terms/EFO_0001187'
            },
            {
                'activity_score': -1.242,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF769REH/',
                'ontology term': 'ontology_terms/EFO_0009747'
            },
            {
                'activity_score': -0.813,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF802FUV/',
                'ontology term': 'ontology_terms/EFO_0002067'
            }
        ]}, {
        'params': {
            'type': 'MPRA_expression_tested',
            'region': 'chr10:100038743-100038963',
            'verbose': 'true'
        },
        'response': [
            {
                'activity_score': 0.226,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF475FKV/',
                'ontology term': [
                    {
                        'uri': 'http://www.ebi.ac.uk/efo/EFO_0001187',
                        'term_id': 'EFO_0001187',
                        'name': 'hepg2',
                        'description': 'human hepatocellular carcinoma (HCC) cells (p53-wt).',
                        'source': 'EFO',
                        'subontology': None
                    }
                ]
            },
            {
                'activity_score': -1.242,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF769REH/',
                'ontology term': [
                    {
                        'uri': 'http://www.ebi.ac.uk/efo/EFO_0009747',
                        'term_id': 'EFO_0009747',
                        'name': 'gm25256',
                        'description': 'Induced pluripotent stem cell line derived from adult skin (leg) fibroblasts; subject clinically normal; wild-type; FISH test: 46, XY.',
                        'source': 'EFO',
                        'subontology': None
                    }
                ]
            },
            {
                'activity_score': -0.813,
                'source': 'ENCODE_MPRA',
                'source_url': 'https://www.encodeproject.org/files/ENCFF802FUV/',
                'ontology term': [
                    {
                        'uri': 'http://www.ebi.ac.uk/efo/EFO_0002067',
                        'term_id': 'EFO_0002067',
                        'name': 'k562',
                        'description': 'Human chronic myeloid leukemia in blast crisis established from the pleural effusion of a 53-year-old woman with chronic myeloid leukemia (CML) in blast crisis in 1970; cells can be used as highly sensitive targets in in-vitro natural killer assays; cells produce hemoglobin; cells carry the Philadelphia chromosome with a b3-a2 fusion gene.',
                        'source': 'EFO',
                        'subontology': None
                    }
                ]
            }
        ]
    }]
}
