import os
import argparse

from adapters.gencode_adapter import Gencode
from adapters.topld_adapter import TopLD
from adapters.gtex_eqtl_adapter import GtexEQtl
from adapters.encode_caqtl_adapter import CAQtl
from adapters.ccre_adapter import CCRE
from adapters.ontologies_adapter import Ontology
from adapters.uniprot_adapter import Uniprot
from adapters.favor_adapter import Favor
from adapters.adastra_asb_adapter import ASB
from adapters.gtex_sqtl_adapter import GtexSQtl
from adapters.encode_enhancer_gene_adapter import EncodeEnhancerGeneLink
from adapters.gaf_adapter import GAF

from db.arango_db import ArangoDB


ADAPTERS = {
    'gencode_genes': Gencode(filepath='./samples/gencode_sample.gtf', type='gene', label='gencode_gene'),
    'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', type='transcript', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed to', label='transcribed_to'),
    'transcribed_from': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed from', label='transcribed_from'),
    'eqtl': GtexEQtl(filepath='./samples/qtl_sample.txt', biological_context='brain_amigdala'),
    'topld': TopLD('chr22', './samples/topld_sample.csv', './samples/topld_info_annotation.csv', ancestry='SAS'),
    'caqtl': CAQtl(filepath='./samples/caqtl-sample.bed'),
    'caqtl_ocr': CAQtl(filepath='./samples/caqtl-sample.bed', label='encode_accessible_dna_region'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'clo_nodes': Ontology(ontology='CLO', type='node'),
    'clo_edges': Ontology(ontology='CLO', type='edge'),
    'uberon_nodes': Ontology(ontology='UBERON', type='node'),
    'uberon_edges': Ontology(ontology='UBERON', type='edge'),
    'cl_nodes': Ontology(ontology='CL', type='node'),
    'cl_edges': Ontology(ontology='CL', type='edge'),
    'hpo_nodes': Ontology(ontology='HPO', type='node'),
    'hpo_edges': Ontology(ontology='HPO', type='edge'),
    'mondo_nodes': Ontology(ontology='MONDO', type='node'),
    'mondo_edges': Ontology(ontology='MONDO', type='edge'),
    'go_nodes_mf': Ontology(ontology='GO', type='node', subontology='molecular_function'),
    'go_edges_mf': Ontology(ontology='GO', type='edge', subontology='molecular_function'),
    'go_nodes_cc': Ontology(ontology='GO', type='node', subontology='cellular_component'),
    'go_edges_cc': Ontology(ontology='GO', type='edge', subontology='cellular_component'),
    'go_nodes_bp': Ontology(ontology='GO', type='node', subontology='biological_process'),
    'go_edges_bp': Ontology(ontology='GO', type='edge', subontology='biological_process'),
    'efo_nodes': Ontology(ontology='EFO', type='node'),
    'efo_edges': Ontology(ontology='EFO', type='edge'),
    'UniProtKB_protein': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz'),
    'UniProtKB_trembl': Uniprot(filepath='./samples/uniprot_trembl_human_sample.dat.gz', type='trembl'),
    'UniProtKB_Translates_To': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translates to', label='UniProtKB_Translates_To'),
    'UniProtKB_Translation_Of': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translation of', label='UniProtKB_Translation_Of'),
    'favor': Favor(filepath='./samples/favor_sample.vcf'),
    'asb': ASB(filepath='./samples/asb/ATF1_HUMAN@HepG2__hepatoblastoma_.tsv', tf_ids='./samples/asb/ADASTRA_TF_uniprot_accession.tsv', cell_ontologies='./samples/asb/ADASTRA_cell_ontologies.tsv'),
    'gtex_splice_qtl': GtexSQtl('./samples/Kidney_Cortex.v8.sqtl_signifpairs.txt.gz', 'Kidney_Cortex'),
    'encode_EpiRaction_regulatory_region': EncodeEnhancerGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'regulatory_region', 'EpiRaction', 'https://www.encodeproject.org/annotations/ENCSR831INH/', 'erythroblast'),
    'encode_EpiRaction_element_gene_link': EncodeEnhancerGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'element_gene_link', 'EpiRaction', 'https://www.encodeproject.org/annotations/ENCSR831INH/', 'erythroblast'),
    'gaf': GAF(filepath='./samples/goa_human_sample.gaf.gz'),
    'gaf_isoform': GAF(filepath='./samples/goa_human_isoform.gaf.gz', gaf_type='human_isoform'),
    'gaf_rna': GAF(filepath='./samples/goa_human_rna.gaf.gz', gaf_type='rna')
}

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--dry-run', action='store_true',
                    help='Dry Run / Print ArangoDB Statements')
parser.add_argument('-a', '--adapter', nargs='*',
                    help='Loads the sampe adata for an adapter', choices=ADAPTERS.keys())
parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')
parser.add_argument('-l', '--create-aliases', action='store_true',
                    help='Creates ArangoDB fuzzy search alisases for a given adapter')

args = parser.parse_args()

dry_run = args.dry_run
create_indexes = args.create_indexes
create_aliases = args.create_aliases
adapters = args.adapter or ADAPTERS.keys()

if not dry_run:
    ArangoDB().setup_dev()

import_cmds = []

for a in adapters:
    adapter = ADAPTERS[a]

    if create_indexes:
        adapter.create_indexes()
    elif create_aliases:
        adapter.create_aliases()
    else:
        adapter.write_file()

        if getattr(adapter, 'SKIP_BIOCYPHER', None):
            exit(0)

        import_cmds.append(adapter.arangodb())

        if adapter.has_indexes():
            print(
                '{} needs indexes. After data loading, please run: python3 dev_setup.py -i -a {}'.format(a, a))

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)
