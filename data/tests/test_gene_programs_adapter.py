import gzip
import json
from unittest.mock import patch

import pytest

from adapters.gene_programs_adapter import GenePrograms
from adapters.writer import SpyWriter


HEADER = 'program_id\tgene\tscore\tprogram_annotation\n'
ROWS = (
    'GP_1\tENSG00000119707\t0.5\tignored GO annotation\n'
    'GP_2\tENSG00000119707\t0.3\tignored GO annotation\n'
    'GP_1\tENSG00000289740\t0.2\tignored GO annotation\n'
)


@pytest.fixture
def metadata():
    with patch('adapters.gene_programs_adapter.get_file_fileset_by_accession_in_arangodb') as lookup:
        lookup.return_value = {
            'class': 'observed data', 'method': 'cNMF', 'file_set_id': 'IGVFDS1435ERVG',
        }
        yield lookup


@pytest.mark.parametrize('compressed', [False, True])
def test_program_nodes(tmp_path, metadata, compressed):
    path = tmp_path / ('IGVFFI9532OEFJ.tsv' + ('.gz' if compressed else ''))
    content = '#description=Top genes\n#sample_summary_short=Combined conditions\n' + HEADER + ROWS
    opener = gzip.open if compressed else open
    with opener(path, 'wt') as output:
        output.write(content)
    writer = SpyWriter()
    with patch.object(writer, 'add_tag') as add_tag:
        GenePrograms(path, writer=writer).process_file()
    docs = [json.loads(row) for row in writer.contents if row.strip()]
    assert len(docs) == 2
    assert [doc['_key'] for doc in docs] == [
        'IGVFFI9532OEFJ_GP_1', 'IGVFFI9532OEFJ_GP_2']
    assert [doc['reported_gene_count'] for doc in docs] == [2, 1]
    assert docs[0]['program_id'] == docs[0]['name'] == 'GP_1'
    assert docs[0]['files_filesets'] == 'files_filesets/IGVFFI9532OEFJ'
    assert docs[0]['class'] == 'observed data'
    assert docs[0]['method'] == docs[0]['label'] == 'cNMF'
    assert all('program_annotation' not in doc for doc in docs)
    metadata.assert_called_once_with('IGVFFI9532OEFJ')
    add_tag.assert_any_call('portal_accessions', 'IGVFFI9532OEFJ')
    add_tag.assert_any_call('portal_accessions', 'IGVFDS1435ERVG')


def test_ids_are_scoped_to_defining_file():
    assert GenePrograms.program_key('IGVFFI9532OEFJ', 'GP_1') != GenePrograms.program_key(
        'IGVFFI0156PMEA', 'GP_1')
    with pytest.raises(ValueError, match='Invalid program ID'):
        GenePrograms.program_key('IGVFFI9532OEFJ', 'GP/1')


@pytest.mark.parametrize('content, error', [
    ('', 'Missing gene-program columns'),
    ('program_id\tgene\nGP_1\tENSG00000119707\n',
     'Missing gene-program columns: score'),
    (HEADER, 'no program definitions'),
    (HEADER + ROWS + 'GP_1\tENSG00000119707\t0.9\t\n', 'Duplicate member'),
    (HEADER + 'GP_1\t\t0.3\t\n', 'Missing gene'),
    (HEADER + '\tENSG00000119707\t0.3\t\n', 'Invalid program ID'),
    (HEADER + 'GP_1\tENSG00000119707\n', 'Malformed gene-program row'),
    (HEADER + 'GP_1\tTP53\t0.3\t\n', 'Invalid Ensembl gene ID'),
    (HEADER + 'GP_1\tENSG00000119707\tnot-a-number\t\n', 'Invalid membership score'),
    (HEADER + 'GP_1\tENSG00000119707\tnan\t\n', 'Non-finite membership score'),
    (HEADER + 'GP_1\tENSG00000119707\tinf\t\n', 'Non-finite membership score'),
    (HEADER + ROWS + 'GP_1\tENSG00000119707.15\t0.9\t\n', 'Duplicate member'),
])
def test_invalid_inputs_write_no_nodes(tmp_path, metadata, content, error):
    path = tmp_path / 'IGVFFI9532OEFJ.tsv'
    path.write_text(content)
    writer = SpyWriter()
    with pytest.raises(ValueError, match=error):
        GenePrograms(path, writer=writer).process_file()
    assert writer.contents == []
    metadata.assert_not_called()


def test_missing_file_metadata(tmp_path, metadata):
    path = tmp_path / 'IGVFFI9532OEFJ.tsv'
    path.write_text(HEADER + ROWS)
    metadata.return_value = None
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Load files_filesets metadata'):
        GenePrograms(path, writer=writer).process_file()
    assert writer.contents == []


def test_other_file_types_are_not_yet_supported(tmp_path):
    with pytest.raises(ValueError, match='Invalid label'):
        GenePrograms(tmp_path / 'IGVFFI7611VVSS.tsv.gz',
                     label='gene_program_regulation')


def test_input_requires_accession_filename(tmp_path):
    with pytest.raises(ValueError, match='filename must begin'):
        GenePrograms(tmp_path / 'programs.tsv')


def test_membership_preserves_scores_and_resolves_node_ids(tmp_path, metadata):
    path = tmp_path / 'IGVFFI9532OEFJ.tsv'
    path.write_text(
        HEADER + ROWS.replace('ENSG00000119707', 'ENSG00000119707.15'))
    node_writer, edge_writer = SpyWriter(), SpyWriter()
    GenePrograms(path, writer=node_writer).process_file()
    with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
        validator.return_value.validate.return_value = True
        GenePrograms(path, label='gene_program_membership',
                     writer=edge_writer).process_file()
    nodes = [json.loads(row) for row in node_writer.contents if row.strip()]
    edges = [json.loads(row) for row in edge_writer.contents if row.strip()]
    assert len(edges) == 3
    assert {edge['_to'] for edge in edges} == {
        f'gene_programs/{node["_key"]}' for node in nodes}
    assert len({edge['_key'] for edge in edges}) == 3
    assert {edge['name'] for edge in edges} == {'is a member of'}
    assert {edge['inverse_name'] for edge in edges} == {'has member'}
    scores = {(edge['_from'], edge['_to'].rsplit('_', 1)[-1])              : edge['score'] for edge in edges}
    assert scores == {
        ('genes/ENSG00000119707', '1'): 0.5,
        ('genes/ENSG00000289740', '1'): 0.2,
        ('genes/ENSG00000119707', '2'): 0.3,
    }
    assert all(edge['_key'].endswith('_membership') for edge in edges)
    assert all('score' not in node and 'members' not in node for node in nodes)
    validator.return_value.validate.assert_any_call('ENSG00000119707')
    validator.return_value.log.assert_called_once()


def test_missing_genes_are_skipped_without_changing_reported_count(tmp_path, metadata):
    path = tmp_path / 'IGVFFI9532OEFJ.tsv'
    path.write_text(HEADER + ROWS)
    writer = SpyWriter()
    with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
        validator.return_value.validate.side_effect = lambda gene: gene == 'ENSG00000119707'
        GenePrograms(path, label='gene_program_membership',
                     writer=writer).process_file()
    edges = [json.loads(row) for row in writer.contents if row.strip()]
    assert len(edges) == 2
    assert {edge['_from'] for edge in edges} == {'genes/ENSG00000119707'}
    node_writer = SpyWriter()
    GenePrograms(path, writer=node_writer).process_file()
    assert json.loads(node_writer.contents[0])['reported_gene_count'] == 2


@pytest.mark.parametrize('score', [0.0, -0.5])
def test_zero_and_negative_membership_scores_are_not_filtered(tmp_path, metadata, score):
    path = tmp_path / 'IGVFFI9532OEFJ.tsv'
    path.write_text(HEADER + f'GP_1\tENSG00000119707\t{score}\t\n')
    writer = SpyWriter()
    with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
        validator.return_value.validate.return_value = True
        GenePrograms(path, label='gene_program_membership',
                     writer=writer).process_file()
    assert json.loads(writer.contents[0])['score'] == score


@pytest.mark.parametrize('accession', ['IGVFFI6391GCJR', 'IGVFFI9532OEFJ', 'IGVFFI0156PMEA'])
def test_biosample_attribution_on_nodes_and_membership(tmp_path, metadata, accession):
    path = tmp_path / f'{accession}.tsv'
    path.write_text(HEADER + ROWS)
    metadata.return_value['samples'] = ['ontology_terms/CL_0000034']
    for label in GenePrograms.ALLOWED_LABELS:
        writer = SpyWriter()
        with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
            validator.return_value.validate.return_value = True
            GenePrograms(path, label=label, writer=writer,
                         validate=True).process_file()
        docs = [json.loads(row) for row in writer.contents if row.strip()]
        for doc in docs:
            if accession == 'IGVFFI6391GCJR':
                assert doc['biosample_term'] == 'ontology_terms/CL_0000115'
            else:
                assert doc['biosample_term'] == 'ontology_terms/CL_0000034'
            assert not any('override' in key or 'note' in key for key in doc)
    assert metadata.return_value['samples'] == ['ontology_terms/CL_0000034']


@pytest.mark.parametrize('samples', [None, []])
@pytest.mark.parametrize('accession', ['IGVFFI9532OEFJ', 'IGVFFI6391GCJR'])
def test_missing_samples_allow_nodes_and_membership(tmp_path, metadata, samples, accession):
    path = tmp_path / f'{accession}.tsv'
    path.write_text(HEADER + ROWS)
    metadata.return_value['samples'] = samples
    for label in GenePrograms.ALLOWED_LABELS:
        writer = SpyWriter()
        with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
            validator.return_value.validate.return_value = True
            GenePrograms(path, label=label, writer=writer,
                         validate=True).process_file()
        docs = [json.loads(row) for row in writer.contents if row.strip()]
        assert docs
        for doc in docs:
            if accession == 'IGVFFI6391GCJR':
                assert doc['biosample_term'] == 'ontology_terms/CL_0000115'
            else:
                assert 'biosample_term' not in doc
