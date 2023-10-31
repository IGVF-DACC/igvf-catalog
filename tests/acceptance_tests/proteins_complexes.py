proteins_complexes = {
    '/proteins/{id}/complexes': [{
        'params_url': {
            'id': 'P23511'
        },
        'params': {
            'verbose': 'false'
        },
        'response': [
            {
                'source': 'EBI',
                'source_url': 'https://www.ebi.ac.uk/complexportal/',
                'complex': 'complexes/CPX-1956'
            }
        ]
    }, {
        'params_url': {
            'id': 'P23511'
        },
        'params': {
            'verbose': 'true'
        },
        'response': [
            {
                'source': 'EBI',
                'source_url': 'https://www.ebi.ac.uk/complexportal/',
                'complex': [
                    {
                        '_id': 'CPX-1956',
                        'complex_name': 'CCAAT-binding factor complex',
                        'alias': [
                            'Nuclear transcription factor Y complex',
                            'NF-Y transcription factor complex',
                            'CCAAT box DNA-binding factor complex',
                            'CBF complex'
                        ],
                        'molecules': [
                            'P23511(1)',
                            'P25208(1)',
                            'Q13952(1)'
                        ],
                        'evidence_code': 'ECO:0000353(physical interaction evidence used in manual assertion)',
                        'experimental_evidence': 'intact:EBI-6672292',
                        'description': 'Transcription factor which binds to the CCAAT box, which occurs in 30% of eukaryotic promoters and appears to be crucial for promoter activity. May also play a role in histone methylation and some acetylation through recruitment of relevant enzymes to active promoters.',
                        'complex_assembly': 'Heterotrimer',
                        'complex_source': "psi-mi:\"MI:0469\"(IntAct)",
                        'reactome_xref': [
                            'R-HSA-381204(identity)'
                        ],
                        'source': 'EBI',
                        'source_url': 'https://www.ebi.ac.uk/complexportal/'
                    }
                ]
            }
        ]

    }],
    '/proteins/complexes': [{
        'params': {
            'name': 'NFYA_HUMAN',
            'verbose': 'false'
        },
        'response': [
            {
                'source': 'EBI',
                'source_url': 'https://www.ebi.ac.uk/complexportal/',
                'complex': 'complexes/CPX-1956'
            }
        ]
    }, {
        'params': {
            'name': 'NFYA_HUMAN',
            'verbose': 'true'
        },
        'response': [
            {
                'source': 'EBI',
                'source_url': 'https://www.ebi.ac.uk/complexportal/',
                'complex': [
                    {
                        '_id': 'CPX-1956',
                        'complex_name': 'CCAAT-binding factor complex',
                        'alias': [
                          'Nuclear transcription factor Y complex',
                            'NF-Y transcription factor complex',
                            'CCAAT box DNA-binding factor complex',
                            'CBF complex'
                        ],
                        'molecules': [
                            'P23511(1)',
                            'P25208(1)',
                            'Q13952(1)'
                        ],
                        'evidence_code': 'ECO:0000353(physical interaction evidence used in manual assertion)',
                        'experimental_evidence': 'intact:EBI-6672292',
                        'description': 'Transcription factor which binds to the CCAAT box, which occurs in 30% of eukaryotic promoters and appears to be crucial for promoter activity. May also play a role in histone methylation and some acetylation through recruitment of relevant enzymes to active promoters.',
                        'complex_assembly': 'Heterotrimer',
                        'complex_source': "psi-mi:\"MI:0469\"(IntAct)",
                        'reactome_xref': [
                            'R-HSA-381204(identity)'
                        ],
                        'source': 'EBI',
                        'source_url': 'https://www.ebi.ac.uk/complexportal/'
                    }
                ]
            }
        ]
    }]
}
