from copy import deepcopy
import gzip
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

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
                     label='unsupported')


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
    for label in ('gene_program', 'gene_program_membership'):
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
    for label in ('gene_program', 'gene_program_membership'):
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


@pytest.mark.parametrize('context', [
    {
        'simple_sample_summaries': ['combined resting and treated cells', 'another summary'],
        'treatments_term_ids': ['CHEBI:15367', 'CHEBI:27732'],
        'perturbation': 'CRISPR interference',
    },
    {},
    {'simple_sample_summaries': None,
        'treatments_term_ids': None, 'perturbation': None},
    {'simple_sample_summaries': [], 'treatments_term_ids': [], 'perturbation': None},
])
def test_file_sample_context_is_shared_by_nodes_and_membership(tmp_path, metadata, context):
    path = tmp_path / 'IGVFFI6391GCJR.tsv'
    path.write_text(HEADER + ROWS)
    metadata.return_value.update(context)
    original_metadata = deepcopy(metadata.return_value)
    summaries = context.get('simple_sample_summaries') or []
    expected = {
        'biological_context': summaries[0] if summaries else None,
        'treatments_term_ids': context.get('treatments_term_ids'),
        'perturbation': context.get('perturbation'),
    }
    for label in ('gene_program', 'gene_program_membership'):
        writer = SpyWriter()
        with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
            validator.return_value.validate.return_value = True
            GenePrograms(path, label=label, writer=writer,
                         validate=True).process_file()
        docs = [json.loads(row) for row in writer.contents if row.strip()]
        assert docs
        for doc in docs:
            assert {field: doc[field] for field in expected} == expected
            assert doc['biosample_term'] == 'ontology_terms/CL_0000115'
    assert metadata.return_value == original_metadata


REGULATOR_COLUMNS = [
    'program_id', 'gene', 'genomic_element', 'genomic_element_coordinates',
    'log2FC', 'reference_group', 'test_statistic', 'p_nominal_nlog10',
    'fdr_nlog10', 'fdr_method',
]
REGULATOR_ROWS = [
    ['GP_1', 'ENSG00000119707.15', 'promoter', 'chr1:100-200,chr1:150-250',
     '-0.5', 'non-targeting', '-2', '3', '2', 'Benjamini-Hochberg'],
    ['GP_2', 'ENSG00000119707', 'promoter', 'chr1:100-200,chr1:150-250',
     '0.25', 'non-targeting', '0.4', '-0.003', '0.2', 'Storey Q-value'],
    ['GP_1', 'ENSG00000289740', 'promoter', 'chr1:100-200',
     '0', 'non-targeting', '0', 'NaN', 'NaN', ''],
]


def regulator_input(tmp_path, accession='IGVFFI7611VVSS', rows=None, compressed=False,
                    reference_accession='IGVFFI9532OEFJ'):
    reference = tmp_path / (reference_accession + '.tsv')
    reference.write_text(HEADER + ROWS)
    path = tmp_path / (accession + ('.tsv.gz' if compressed else '.tsv'))
    opener = gzip.open if compressed else open
    with opener(path, 'wt') as output:
        output.write('#description=regulator effects\n' +
                     '\t'.join(REGULATOR_COLUMNS) + '\n')
        for row in REGULATOR_ROWS if rows is None else rows:
            output.write('\t'.join(row) + '\n')
    return path, reference


def parse_regulators(path, label, valid_gene=lambda gene: True, **kwargs):
    reference_name = 'IGVFFI7611VVSS.tsv' if label in (
        'regulator_correlation', 'genomic_element_regulator_correlation') else 'IGVFFI9532OEFJ.tsv'
    kwargs.setdefault('reference_filepath', path.parent / reference_name)
    writer = SpyWriter()
    with patch('adapters.gene_programs_adapter.GeneValidator') as validator:
        validator.return_value.validate.side_effect = valid_gene
        GenePrograms(path, label=label, writer=writer,
                     validate=True, **kwargs).process_file()
    return [json.loads(row) for row in writer.contents if row.strip()]


@pytest.mark.parametrize('accession,reference_accession', [
    ('IGVFFI7611VVSS', 'IGVFFI9532OEFJ'),
    ('IGVFFI7887NYRJ', 'IGVFFI0156PMEA'),
    ('IGVFFI2627GHHU', 'IGVFFI0156PMEA'),
    ('IGVFFI2454MTFS', 'IGVFFI0156PMEA'),
    ('IGVFFI8214DMKC', 'IGVFFI6391GCJR'),
    ('IGVFFI4053SPMD', 'IGVFFI6391GCJR'),
    ('IGVFFI9940ZZPJ', 'IGVFFI6391GCJR'),
    ('IGVFFI5389NMWB', 'IGVFFI6391GCJR'),
])
def test_regulation_and_elements_link_to_shared_programs(
        tmp_path, metadata, accession, reference_accession, caplog):
    config_path = Path(__file__).resolve(
    ).parents[1] / 'data_sources/data_sources.yaml'
    config = yaml.safe_load(config_path.read_text())
    for source in ('gene gene program regulation IGVF', 'genomic element gene program regulators IGVF'):
        entry = config[source]
        assert '--reference-filepath {reference_filepath}' in entry['command']
        mappings = entry['file_mappings']
        assert len(mappings) == 8
        pair = next(item for item in mappings if Path(
            item['datafile']).name == accession + '.tsv.gz')
        assert Path(pair['reference_filepath']
                    ).name == reference_accession + '.tsv.gz'
    path, reference = regulator_input(tmp_path, accession, compressed=True,
                                      reference_accession=reference_accession)
    metadata.return_value.update({
        'simple_sample_summaries': ['condition-specific sample'],
        'samples': ['ontology_terms/EFO_0009747'],
        'perturbation': 'CRISPR interference', 'treatments_term_ids': [],
    })
    nodes = parse_regulators(path, 'genomic_element',
                             reference_filepath=reference)
    edges = parse_regulators(
        path, 'gene_program_regulation', reference_filepath=reference)
    # Reuse intervals across programs, preserving shared-interval gene associations.
    assert len(nodes) == 3
    # Multiple promoters do not duplicate the gene-level effect.
    assert len(edges) == 3
    assert {(node['start'], node['end'])
            for node in nodes} == {(100, 200), (150, 250)}
    assert {node['promoter_of'] for node in nodes} == {
        'genes/ENSG00000119707', 'genes/ENSG00000289740'}
    handles = {'genomic_elements/' + node['_key'] for node in nodes}
    assert {
        handle for edge in edges for handle in edge['genomic_elements']} == handles
    for edge in edges:
        assert edge['_to'].startswith(
            'gene_programs/' + reference.stem + '_GP_')
        assert edge['_key'].startswith(accession + '_')
        assert edge['files_filesets'] == 'files_filesets/' + accession
        assert edge['name'] == 'regulates' and edge['inverse_name'] == 'regulated by'
        assert edge['biosample_term'] == 'ontology_terms/EFO_0009747'
        assert edge['biological_context'] == 'condition-specific sample'
        assert 'score' not in edge
    assert edges[0]['log2FC'] == -0.5 and edges[0]['test_statistic'] == -2
    assert [edge['significant'] for edge in edges] == [True, False, None]
    assert edges[1]['neg_log10_pvalue'] == -0.003
    assert edges[1]['fdr_method'] == 'Storey Q-value'
    assert edges[2]['neg_log10_pvalue'] is None
    assert edges[2]['neg_log10_pvalue_adj'] is None
    assert 'negative p_nominal_nlog10' in caplog.text


@pytest.mark.parametrize('adjusted, significant', [
    (str(GenePrograms.SIGNIFICANCE_NLOG10),
     False), ('2', True), ('0', False), ('N/A', None),
])
def test_regulator_significance_boundary(tmp_path, metadata, adjusted, significant):
    rows = deepcopy(REGULATOR_ROWS[:1])
    rows[0][8] = adjusted
    path, _ = regulator_input(tmp_path, rows=rows)
    edges = parse_regulators(path, 'gene_program_regulation')
    assert edges[0]['significant'] is significant


@pytest.mark.parametrize('column,value,error', [
    (0, 'GP_99', 'is not defined'),
    (1, 'TP53', 'Invalid regulator Ensembl'),
    (2, 'unknown', 'Unsupported regulator genomic_element'),
    (3, '', 'Invalid regulator coordinates'),
    (3, 'chr1:200-100', 'Invalid regulator interval'),
    (3, 'chr1:0-0', 'Invalid regulator interval'),
    (3, 'chr1:100-200,invalid', 'Invalid regulator coordinates'),
    (4, 'inf', 'Non-finite regulator log2FC'),
    (5, '', 'Missing reference_group'),
    (6, 'invalid', 'Invalid regulator test_statistic'),
    (8, '-0.1', 'Negative fdr_nlog10'),
])
def test_invalid_regulator_rows_fail(tmp_path, metadata, column, value, error):
    rows = deepcopy(REGULATOR_ROWS[:1])
    rows[0][column] = value
    path, _ = regulator_input(tmp_path, rows=rows)
    for label in ('gene_program_regulation', 'genomic_element'):
        with pytest.raises(ValueError, match=error):
            parse_regulators(path, label)


def test_duplicate_regulator_pairs_fail(tmp_path, metadata):
    path, _ = regulator_input(
        tmp_path, rows=[REGULATOR_ROWS[0], REGULATOR_ROWS[0]])
    with pytest.raises(ValueError, match='Duplicate regulator result'):
        parse_regulators(path, 'gene_program_regulation')


def test_unknown_regulator_genes_skip_edges_and_elements(tmp_path, metadata):
    path, _ = regulator_input(tmp_path)
    for label in ('gene_program_regulation', 'genomic_element'):
        assert parse_regulators(
            path, label, valid_gene=lambda gene: False) == []


@pytest.mark.parametrize('label', ['gene_program_regulation', 'genomic_element'])
def test_regulator_reference_is_required(tmp_path, metadata, label):
    path, reference = regulator_input(tmp_path)
    with pytest.raises(ValueError, match='require program definitions via --reference-filepath'):
        parse_regulators(path, label, reference_filepath=None)
    other = tmp_path / 'elsewhere'
    other.mkdir()
    relocated = other / reference.name
    reference.rename(relocated)
    with pytest.raises(ValueError, match='Missing program definitions'):
        parse_regulators(path, label, reference_filepath=reference)
    assert len(parse_regulators(
        path, label, reference_filepath=relocated)) == 3
    with pytest.raises(ValueError, match='Missing gene-program columns: score'):
        parse_regulators(path, label, reference_filepath=path)
    invalid = other / 'definitions.tsv'
    invalid.write_text(HEADER + ROWS)
    with pytest.raises(ValueError, match='filename must begin with its IGVF file accession'):
        parse_regulators(path, label, reference_filepath=invalid)


def test_new_regulator_and_definition_accessions_need_no_adapter_mapping(tmp_path, metadata):
    path, reference = regulator_input(tmp_path, accession='IGVFFI0000AAAA',
                                      reference_accession='IGVFFI0001AAAA')
    edges = parse_regulators(
        path, 'gene_program_regulation', reference_filepath=reference)
    assert len(edges) == 3
    assert all(edge['_to'].startswith('gene_programs/IGVFFI0001AAAA_')
               for edge in edges)


def test_duplicate_interval_in_one_result_is_emitted_once(tmp_path, metadata):
    rows = deepcopy(REGULATOR_ROWS[:1])
    rows[0][3] = 'chr1:0-10,chr1:0-10'
    path, _ = regulator_input(tmp_path, rows=rows)
    assert len(parse_regulators(path, 'genomic_element')) == 1
    assert len(parse_regulators(path, 'gene_program_regulation')
               [0]['genomic_elements']) == 1


def test_edge_schema_keeps_membership_and_regulation_distinct(tmp_path, metadata):
    path, _ = regulator_input(tmp_path)
    edge = parse_regulators(path, 'gene_program_regulation')[0]
    adapter = GenePrograms(
        path, label='gene_program_regulation', validate=True)
    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc({**edge, 'score': 0.4})
    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc({**edge, 'inverse_name': 'has member'})
    edge.pop('genomic_elements')
    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc(edge)


CORRELATION_COLUMNS = [
    'gene_1', 'genomic_element_1', 'genomic_element_coordinates_1',
    'gene_2', 'genomic_element_2', 'genomic_element_coordinates_2', 'pearson_correlation',
]
CORRELATION_ROWS = [
    ['ENSG00000119707.15', 'promoter', 'chr1:0-100,chr1:50-150',
     'ENSG00000289740', 'promoter', 'chr1:0-100', '0.5'],
    ['ENSG00000289740', 'promoter', 'chr1:0-100',
     'ENSG00000119707', 'promoter', 'chr1:50-150,chr1:0-100', '0.5'],
]


def correlation_input(tmp_path, rows=None):
    upstream_rows = deepcopy(REGULATOR_ROWS)
    upstream_rows[0][3] = upstream_rows[1][3] = 'chr1:0-100,chr1:50-150'
    upstream_rows[2][3] = 'chr1:0-100'
    regulator_input(tmp_path, rows=upstream_rows)
    path = tmp_path / 'IGVFFI5227NZPM.tsv.gz'
    with gzip.open(path, 'wt') as output:
        output.write('# correlation elements\n' +
                     '\t'.join(CORRELATION_COLUMNS) + '\n')
        for row in CORRELATION_ROWS if rows is None else rows:
            output.write('\t'.join(row) + '\n')
    return path


def test_correlation_elements_use_both_sides_and_upstream_provenance(tmp_path, metadata):
    path = correlation_input(tmp_path)
    nodes = parse_regulators(path, 'genomic_element_regulator_correlation')
    assert len(nodes) == 3
    assert {node['promoter_of'] for node in nodes} == {
        'genes/ENSG00000119707', 'genes/ENSG00000289740'}
    assert {(node['start'], node['end'])
            for node in nodes} == {(0, 100), (50, 150)}
    assert all(node['_key'].endswith('_IGVFFI7611VVSS') for node in nodes)
    assert all(node['files_filesets'] ==
               'files_filesets/IGVFFI7611VVSS' for node in nodes)
    assert all(node['source_url'].endswith('/IGVFFI7611VVSS/')
               for node in nodes)
    assert all('pearson_correlation' not in node for node in nodes)
    kept = parse_regulators(path, 'genomic_element_regulator_correlation',
                            valid_gene=lambda gene: gene == 'ENSG00000289740')
    assert len(kept) == 1
    assert kept[0]['promoter_of'] == 'genes/ENSG00000289740'


@pytest.mark.parametrize('column,value,error', [
    (0, 'invalid', 'Invalid regulator Ensembl'),
    (3, 'invalid', 'Invalid regulator Ensembl'),
    (4, 'unknown', 'Unsupported regulator genomic_element'),
    (5, 'chr1:20-10', 'Invalid regulator interval'),
    (2, 'invalid', 'Invalid regulator coordinates'),
])
def test_invalid_correlation_elements_fail(tmp_path, metadata, column, value, error):
    rows = deepcopy(CORRELATION_ROWS[:1])
    rows[0][column] = value
    path = correlation_input(tmp_path, rows)
    with pytest.raises(ValueError, match=error):
        parse_regulators(path, 'genomic_element_regulator_correlation')


def test_empty_correlation_elements_fail(tmp_path, metadata):
    path = correlation_input(tmp_path, [])
    with pytest.raises(ValueError, match='contains no results'):
        parse_regulators(path, 'genomic_element_regulator_correlation')


def test_correlation_elements_data_source_covers_all_correlation_files():
    config_path = Path(__file__).resolve(
    ).parents[1] / 'data_sources/data_sources.yaml'
    config = yaml.safe_load(config_path.read_text())
    source = config['genomic element gene program regulator correlations IGVF']
    assert source['file_mappings'] == config['gene gene regulator correlation IGVF']['file_mappings']
    assert len(source['file_mappings']) == 8
    assert '--label genomic_element_regulator_correlation' in source['command']
    assert '--reference-filepath {reference_filepath}' in source['command']


def test_core_outputs_do_not_require_correlation_files(tmp_path, metadata):
    path, reference = regulator_input(tmp_path)
    assert set(tmp_path.iterdir()) == {path, reference}
    for label in ('gene_program', 'gene_program_membership'):
        writer = SpyWriter()
        with patch('adapters.gene_programs_adapter.GeneValidator') as genes:
            genes.return_value.validate.return_value = True
            GenePrograms(reference, label=label, writer=writer,
                         validate=True).process_file()
        assert any(line.strip() for line in writer.contents)
    nodes = parse_regulators(path, 'genomic_element',
                             reference_filepath=reference)
    edges = parse_regulators(
        path, 'gene_program_regulation', reference_filepath=reference)
    handles = {'genomic_elements/' + node['_key'] for node in nodes}
    assert {
        handle for edge in edges for handle in edge['genomic_elements']} == handles
    assert len(nodes) == len(edges) == 3


def program_correlation_input(tmp_path, rows=None, accession='IGVFFI9407YNQA',
                              reference_accession='IGVFFI9532OEFJ'):
    reference = tmp_path / (reference_accession + '.tsv')
    reference.write_text(HEADER + ROWS)
    path = tmp_path / (accession + '.tsv.gz')
    with gzip.open(path, 'wt') as output:
        output.write(
            '# program correlations\nprogram_1_id\tprogram_2_id\tpearson_correlation\n')
        for row in [('GP_2', 'GP_1', '-0.5')] if rows is None else rows:
            output.write('\t'.join(row) + '\n')
    return path, reference


@pytest.mark.parametrize('accession,reference_accession', [
    ('IGVFFI9407YNQA', 'IGVFFI9532OEFJ'),
    ('IGVFFI9545WAUX', 'IGVFFI0156PMEA'),
    ('IGVFFI5706ASJE', 'IGVFFI0156PMEA'),
    ('IGVFFI5778ELFM', 'IGVFFI0156PMEA'),
    ('IGVFFI5671ZTPF', 'IGVFFI6391GCJR'),
    ('IGVFFI0574VVJA', 'IGVFFI6391GCJR'),
    ('IGVFFI3823LYPH', 'IGVFFI6391GCJR'),
    ('IGVFFI3188WQFI', 'IGVFFI6391GCJR'),
])
def test_program_correlations_reference_existing_programs(tmp_path, metadata, accession, reference_accession):
    config = yaml.safe_load((Path(__file__).resolve(
    ).parents[1] / 'data_sources/data_sources.yaml').read_text())
    source = config['gene program gene program correlation IGVF']
    assert '--label gene_program_correlation' in source['command']
    assert '--reference-filepath {reference_filepath}' in source['command']
    assert len(source['file_mappings']) == 8
    mapping = next(m for m in source['file_mappings'] if Path(
        m['datafile']).name == accession + '.tsv.gz')
    assert Path(mapping['reference_filepath']
                ).name == reference_accession + '.tsv.gz'
    path, reference = program_correlation_input(
        tmp_path, accession=accession, reference_accession=reference_accession)
    metadata.return_value.update({'samples': ['ontology_terms/EFO_0009747'],
                                  'simple_sample_summaries': ['condition-specific sample'],
                                  'treatments_term_ids': [], 'perturbation': 'CRISPR interference'})
    edges = parse_regulators(
        path, 'gene_program_correlation', reference_filepath=reference)
    assert len(edges) == 1
    edge = edges[0]
    assert edge['_from'] == f'gene_programs/{reference_accession}_GP_1'
    assert edge['_to'] == f'gene_programs/{reference_accession}_GP_2'
    assert edge['name'] == edge['inverse_name'] == 'correlated with'
    assert edge['pearson_correlation'] == -0.5
    assert edge['files_filesets'] == 'files_filesets/' + accession
    assert edge['biosample_term'] == 'ontology_terms/EFO_0009747'
    assert edge['biological_context'] == 'condition-specific sample'
    assert edge['perturbation'] == 'CRISPR interference'
    assert edge['treatments_term_ids'] == []
    assert edge['_key'].startswith(accession + '_' + reference_accession + '_')
    assert not {'genomic_elements', 'significant', 'score'} & edge.keys()


def test_program_correlations_are_symmetric(tmp_path, metadata):
    path, reference = program_correlation_input(tmp_path)
    first = parse_regulators(
        path, 'gene_program_correlation', reference_filepath=reference)
    program_correlation_input(
        tmp_path, [('GP_1', 'GP_2', '-0.5'), ('GP_2', 'GP_1', '-0.5')])
    assert parse_regulators(path, 'gene_program_correlation',
                            reference_filepath=reference) == first
    other, _ = program_correlation_input(tmp_path, accession='IGVFFI0000AAAA')
    second = parse_regulators(
        other, 'gene_program_correlation', reference_filepath=reference)
    assert second[0]['_key'] != first[0]['_key']


@pytest.mark.parametrize('rows,error', [
    ([], 'contains no results'),
    ([('GP_99', 'GP_1', '0.1')], 'is not defined'),
    ([('GP_1', 'GP_99', '0.1')], 'is not defined'),
    ([('GP_1', 'GP_2', 'NA')], 'Invalid Pearson correlation'),
    ([('GP_1', 'GP_2', 'nan')], 'must be finite'),
    ([('GP_1', 'GP_2', 'inf')], 'must be finite'),
    ([('GP_1', 'GP_2', '1.01')], 'within'),
    ([('GP_1', 'GP_2', '-1.01')], 'within'),
    ([('GP_1', 'GP_2', '0.1'), ('GP_2', 'GP_1', '0.2')],
     'Conflicting Pearson correlations'),
])
def test_invalid_program_correlations_fail(tmp_path, metadata, rows, error):
    path, reference = program_correlation_input(tmp_path, rows)
    with pytest.raises(ValueError, match=error):
        parse_regulators(path, 'gene_program_correlation',
                         reference_filepath=reference)


@pytest.mark.parametrize('value', ['-1', '0', '1'])
def test_program_correlation_bounds_and_zero_are_retained(tmp_path, metadata, value):
    path, reference = program_correlation_input(
        tmp_path, [('GP_1', 'GP_2', value)])
    edges = parse_regulators(
        path, 'gene_program_correlation', reference_filepath=reference)
    assert edges[0]['pearson_correlation'] == float(value)


def test_program_correlations_require_reference_and_validate_schema(tmp_path, metadata):
    path, reference = program_correlation_input(tmp_path)
    with pytest.raises(ValueError, match='require program definitions'):
        parse_regulators(path, 'gene_program_correlation',
                         reference_filepath=None)
    with pytest.raises(ValueError, match='Missing program definitions'):
        parse_regulators(path, 'gene_program_correlation',
                         reference_filepath=tmp_path / 'missing.tsv')
    edge = parse_regulators(path, 'gene_program_correlation',
                            reference_filepath=reference)[0]
    adapter = GenePrograms(path, label='gene_program_correlation',
                           reference_filepath=reference, validate=True)
    for patch_props in ({'_from': 'genes/ENSG00000119707'}, {'pearson_correlation': 2}, {'inverse_name': 'regulates'}):
        with pytest.raises(ValueError, match='Document validation failed'):
            adapter.validate_doc({**edge, **patch_props})


def test_regulator_correlations_share_upstream_elements(tmp_path, metadata):
    path = correlation_input(tmp_path, CORRELATION_ROWS[:1])
    upstream = tmp_path / 'IGVFFI7611VVSS.tsv'
    metadata.side_effect = lambda accession: {
        'class': 'observed data', 'method': 'Perturb-seq',
        'samples': ['ontology_terms/EFO_0009747'],
        'simple_sample_summaries': [accession], 'perturbation': 'CRISPR interference',
        'treatments_term_ids': [],
    }
    edges = parse_regulators(path, 'regulator_correlation')
    nodes = parse_regulators(path, 'genomic_element_regulator_correlation')
    upstream_nodes = parse_regulators(upstream, 'genomic_element')
    assert sorted(nodes, key=lambda node: node['_key']) == sorted(
        upstream_nodes, key=lambda node: node['_key'])
    assert len(edges) == 1
    edge = edges[0]
    assert edge['_from'] == 'genes/ENSG00000119707'
    assert edge['_to'] == 'genes/ENSG00000289740'
    assert edge['name'] == edge['inverse_name'] == 'correlated with'
    assert edge['pearson_correlation'] == 0.5
    assert edge['files_filesets'] == 'files_filesets/IGVFFI5227NZPM'
    assert edge['biological_context'] == 'IGVFFI5227NZPM'
    handles = {'genomic_elements/' + node['_key']: node for node in nodes}
    assert set(edge['genomic_elements_from'] +
               edge['genomic_elements_to']) == set(handles)
    for suffix, endpoint in [('from', '_from'), ('to', '_to')]:
        assert all(handles[handle]['promoter_of'] == edge[endpoint]
                   for handle in edge['genomic_elements_' + suffix])
    correlation_input(tmp_path, [CORRELATION_ROWS[1]])
    assert parse_regulators(path, 'regulator_correlation') == edges
    assert parse_regulators(path, 'regulator_correlation',
                            valid_gene=lambda gene: gene == 'ENSG00000119707') == []


@pytest.mark.parametrize('value', ['-1', '0', '1'])
def test_regulator_correlation_values_retained(tmp_path, metadata, value):
    rows = deepcopy(CORRELATION_ROWS[:1])
    rows[0][-1] = value
    path = correlation_input(tmp_path, rows)
    assert parse_regulators(path, 'regulator_correlation')[
        0]['pearson_correlation'] == float(value)


@pytest.mark.parametrize('value', ['NA', 'nan', 'inf', '-inf', '1.01', '-1.01'])
def test_invalid_regulator_correlation_values_fail(tmp_path, metadata, value):
    rows = deepcopy(CORRELATION_ROWS[:1])
    rows[0][-1] = value
    path = correlation_input(tmp_path, rows)
    with pytest.raises(ValueError, match='Pearson correlation'):
        parse_regulators(path, 'regulator_correlation')


@pytest.mark.parametrize('label', ['regulator_correlation', 'genomic_element_regulator_correlation'])
def test_regulator_correlation_upstream_checks(tmp_path, metadata, label):
    path = correlation_input(tmp_path, CORRELATION_ROWS[:1])
    with pytest.raises(ValueError, match='require upstream regulator results'):
        parse_regulators(path, label, reference_filepath=None)
    with pytest.raises(ValueError, match='Missing upstream regulator results'):
        parse_regulators(
            path, label, reference_filepath=tmp_path / 'missing.tsv')
    with pytest.raises(ValueError, match='Missing gene-program columns'):
        parse_regulators(
            path, label, reference_filepath=tmp_path / 'IGVFFI9532OEFJ.tsv')
    rows = deepcopy(CORRELATION_ROWS[:1])
    rows[0][2] = 'chr1:0-101'
    correlation_input(tmp_path, rows)
    with pytest.raises(ValueError, match='do not match'):
        parse_regulators(path, label)
    rows[0][0] = 'ENSG00000000001'
    correlation_input(tmp_path, rows)
    with pytest.raises(ValueError, match='is not defined'):
        parse_regulators(path, label)


def test_duplicate_regulator_correlations_fail_including_reverse(tmp_path, metadata):
    path = correlation_input(tmp_path)
    with pytest.raises(ValueError, match='Duplicate regulator correlation pair'):
        parse_regulators(path, 'regulator_correlation')
    correlation_input(tmp_path, [CORRELATION_ROWS[0]] * 2)
    with pytest.raises(ValueError, match='Duplicate regulator correlation pair'):
        parse_regulators(path, 'regulator_correlation')


def test_regulator_correlation_pair_tracking_distinguishes_diagonal(tmp_path, metadata):
    a = CORRELATION_ROWS[0][:3]
    b = CORRELATION_ROWS[0][3:6]
    path = correlation_input(
        tmp_path, [a + a + ['1'], a + b + ['0.5'], b + b + ['1']])
    edges = parse_regulators(path, 'regulator_correlation')
    assert len(edges) == len({edge['_key'] for edge in edges}) == 3


def test_regulator_correlation_schema_references_and_empty_input(tmp_path, metadata):
    path = correlation_input(tmp_path, CORRELATION_ROWS[:1])
    edge = parse_regulators(path, 'regulator_correlation')[0]
    adapter = GenePrograms(path, label='regulator_correlation', validate=True)
    for properties in ({'_from': 'gene_programs/GP_1'}, {'pearson_correlation': 2},
                       {'genomic_elements_from': []}, {'genomic_elements_to': ['genes/ENSG00000119707']}):
        with pytest.raises(ValueError, match='Document validation failed'):
            adapter.validate_doc({**edge, **properties})
    correlation_input(tmp_path, [])
    with pytest.raises(ValueError, match='contains no results'):
        parse_regulators(path, 'regulator_correlation')


@pytest.mark.parametrize('accession,upstream', [
    ('IGVFFI5227NZPM', 'IGVFFI7611VVSS'), ('IGVFFI3821MANP', 'IGVFFI7887NYRJ'),
    ('IGVFFI6502THLB', 'IGVFFI2627GHHU'), ('IGVFFI9392SDHV', 'IGVFFI2454MTFS'),
    ('IGVFFI1127PXEP', 'IGVFFI8214DMKC'), ('IGVFFI3541QUUN', 'IGVFFI4053SPMD'),
    ('IGVFFI6275JIJY', 'IGVFFI9940ZZPJ'), ('IGVFFI5745PRRI', 'IGVFFI5389NMWB'),
])
def test_regulator_correlation_mappings(accession, upstream):
    config = yaml.safe_load((Path(__file__).resolve(
    ).parents[1] / 'data_sources/data_sources.yaml').read_text())
    source = config['gene gene regulator correlation IGVF']
    assert '--label regulator_correlation' in source['command']
    assert '--reference-filepath {reference_filepath}' in source['command']
    pair = next(m for m in source['file_mappings'] if Path(
        m['datafile']).name == accession + '.tsv.gz')
    assert Path(pair['reference_filepath']).name == upstream + '.tsv.gz'
