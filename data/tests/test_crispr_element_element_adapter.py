import gzip
import json
from unittest.mock import patch

import pytest
from adapters.CRISPR_element_element_adapter import CRISPRElementElement
from adapters.writer import SpyWriter

MODULE = 'adapters.CRISPR_element_element_adapter'
SAMPLE = './samples/crispr_element_element.example.tsv.gz'


def parse(label, filepath=SAMPLE):
    writer = SpyWriter()
    with patch(f'{MODULE}.GeneValidator') as validator, patch(f'{MODULE}.get_file_fileset_by_accession_in_arangodb') as metadata:
        validator.return_value.validate.return_value = True
        metadata.return_value = {
            'method': 'Perturb-seq', 'class': 'observed data',
            'crispr_modality': 'interference',
            'simple_sample_summaries': ['hTERT RPE-1 cell'],
            'samples': ['ontology_terms/CLO_0004290'],
            'treatments_term_ids': None, 'file_set_id': 'IGVFDS1890GPOK',
        }
        CRISPRElementElement(
            filepath, label, 'https://api.data.igvf.org/tabular-files/IGVFFI2419ZSGC/', writer, validate=True).process_file()
    return [json.loads(item) for item in writer.contents if item.strip()]


def test_nodes_and_edges():
    nodes = parse('genomic_element')
    edges = parse('genomic_element_genomic_element')
    assert len(nodes) == 4
    assert len(edges) == 3
    promoters = [node for node in nodes if 'promoter_of' in node]
    assert len(promoters) == 1
    assert promoters[0]['promoter_of'] == 'genes/ENSG00000100811'
    assert promoters[0]['start'] == 100238144
    ids = {f'genomic_elements/{node["_key"]}' for node in nodes}
    assert all(edge['_from'] in ids and edge['_to'] in ids for edge in edges)
    assert edges[0]['log2FC'] == pytest.approx(4.777302097678887)
    assert 'z_score' not in edges[0]
    assert edges[2]['p_value_adj'] > 0.05
    assert edges[2]['significant'] is True


@pytest.mark.parametrize('change,match', [('duplicate', 'Duplicate promoter-peak'), ('gene', 'Invalid promoter gene'), ('interval', 'Invalid genomic interval'), ('nan', 'Non-finite'), ('pvalue', 'P-values must'), ('header', 'missing columns')])
def test_invalid_input(tmp_path, change, match):
    with gzip.open(SAMPLE, 'rt') as stream:
        lines = stream.readlines()
    row = lines[1].rstrip('\n').split('\t')
    if change == 'duplicate':
        lines.append(lines[1])
    elif change == 'header':
        lines[0] = lines[0].replace('effect_score', 'unknown')
    else:
        index, value = {'gene': (8, 'YY1'), 'interval': (
            5, '-1'), 'nan': (0, 'nan'), 'pvalue': (2, '1.1')}[change]
        row[index] = value
        lines[1] = '\t'.join(row) + '\n'
    path = tmp_path / 'input.tsv.gz'
    with gzip.open(path, 'wt') as stream:
        stream.writelines(lines)
    with pytest.raises(ValueError, match=match):
        parse('genomic_element_genomic_element', path)
