transcripts = {
    '/transcripts': [{
        'params': {
            'region': 'chr1:711800-740000',
            'transcript_type': 'processed_transcript'
        },
        'response': [{
            '_id': 'ENST00000414688',
            'transcript_type': 'processed_transcript',
            'chr': 'chr1',
            'start': 711866,
            'end': 732212,
            'transcript_name': 'ENST00000414688',
            'gene_name': 'ENSG00000230021',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://www.gencodegenes.org/human/'
        }, {
            '_id': 'ENST00000447954',
            'transcript_type': 'processed_transcript',
            'chr': 'chr1',
            'start': 720052,
            'end': 724564,
            'transcript_name': 'ENST00000447954',
            'gene_name': 'ENSG00000230021',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://www.gencodegenes.org/human/'
        }]
    }],
    '/transcripts/{id}': [{
        'params_url': {
            'id': 'ENST00000447954'
        },
        'params': {},
        'response': {
            '_id': 'ENST00000447954',
            'transcript_type': 'processed_transcript',
            'chr': 'chr1',
            'start': 720052,
            'end': 724564,
            'transcript_name': 'ENST00000447954',
            'gene_name': 'ENSG00000230021',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://www.gencodegenes.org/human/'
        }
    }]
}
