genes = {
    '/genes': [{
        'params': {
            'gene_name': 'ATF3',
            'region': 'chr1:212565300-212620800',
            'alias': 'HGNC:785',
            'gene_type': 'protein_coding'
        },
        'response': [{
            '_id': 'ENSG00000162772',
            'chr': 'chr1',
            'start': 212565333,
            'end': 212620777,
            'gene_type': 'protein_coding',
            'gene_name': 'ATF3',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://www.gencodegenes.org/human/',
            'alias': [
                'ATF3',
                'cAMP-dependent transcription factor ATF-3',
                'cyclic AMP-dependent transcription factor ATF-3',
                'activating transcription factor 3',
                'HGNC:785'
            ]
        }]
    }, {
        'params': {
            'region': 'chr17:39252662-39402523'
        },
        'response': [
            {
                '_id': 'ENSG00000266469',
                'chr': 'chr17',
                'start': 39401792,
                'end': 39406233,
                'gene_type': 'lncRNA',
                'gene_name': 'ENSG00000266469',
                'source': 'GENCODE',
                'version': 'v43',
                'source_url': 'https://www.gencodegenes.org/human/',
                'alias': None
            },
            {
                '_id': 'ENSG00000108306',
                'chr': 'chr17',
                'start': 39252662,
                'end': 39402523,
                'gene_type': 'protein_coding',
                'gene_name': 'FBXL20',
                'source': 'GENCODE',
                'version': 'v43',
                'source_url': 'https://www.gencodegenes.org/human/',
                'alias': [
                    'FBXL20',
                    'F-box protein FBL2',
                    'F-box and leucine rich repeat protein 20',
                    'HGNC:24679',
                    'Fbl2',
                    'Fbl20',
                    'F-box/LRR-repeat protein 20'
                ]
            }
        ]
    }],
    '/genes/{id}': [{
        'params_url': {
            'id': 'ENSG00000187642'
        },
        'params': {},
        'response': {
            '_id': 'ENSG00000187642',
            'chr': 'chr1',
            'start': 975197,
            'end': 982117,
            'gene_type': 'protein_coding',
            'gene_name': 'PERM1',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://www.gencodegenes.org/human/',
            'alias': [
                'PPARGC1 and ESRR-induced regulator in muscle 1',
                'PPARGC1 and ESRR induced regulator, muscle 1',
                'HGNC:28208',
                'PERM1',
                'PGC-1 and ERR-induced regulator in muscle 1',
                'C1orf170',
                'pGC-1 and ERR-induced regulator in muscle protein 1',
                'peroxisome proliferator-activated receptor gamma coactivator 1 and estrogen-related receptor-induced regulator in muscle 1',
                'PGC-1 and ERR-induced regulator in muscle protein 1'
            ]
        }
    }]
}
