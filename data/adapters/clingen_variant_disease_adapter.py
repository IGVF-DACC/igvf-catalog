import csv
import pickle
import hashlib
import json
import os
from typing import Optional

from db.arango_db import ArangoDB
from adapters.writer import Writer

# Example row from variant_pathogenicity.tsv
# ClinVar Variation Id	chr	start	stop	Gene ID	HGNC Gene Symbol	Mondo Id	Disease	Mode of Inheritance	Assertion	Summary of interpretation	PubMed Articles	Evidence Repo Link	Retracted	Allele	HGVS Expressions	Allele Registry Id
# 586	12	102917130	102917130	ENSG00000171759	PAH	MONDO:0009861	phenylketonuria	Autosomal recessive inheritance	Pathogenic	PAH-specific ACMG/AMP criteria applied: PM2: gnomAD MAF=0.00002; PP4_Moderate: Seen in PKU patients. BH4 disorders ruled out. (PMID:2574002); PS3: <3% (PMID:9450897). PM3: Detected in trans with known pathogenic variants. In summary this variant meets criteria to be classified as pathogenic for phenylketonuria in an autosomal recessive manner based on the ACMG/AMP criteria applied as specified by the PAH Expert Panel: (PM2, PM3, PP4_Moderate, PS3). Updated to reflect new PVS1 recommendations.	\
# 2574002, 2574002, 9450897	https://erepo.genome.network/evrepo/ui/classification/CA114360/MONDO:0009861/006	FALSE	[T/A/C]	NM_000277.2:c.1A>G, NC_000012.12:g.102917130T>C, CM000674.2:g.102917130T>C, NC_000012.11:g.103310908T>C, CM000674.1:g.103310908T>C, NC_000012.10:g.101835038T>C, NG_008690.1:g.5473A>G, NG_008690.2:g.46281A>G, NM_000277.1:c.1A>G, XM_011538422.1:c.1A>G, NM_001354304.1:c.1A>G, XM_017019370.2:c.1A>G, NM_000277.3:c.1A>G, ENST00000307000.7:c.-147A>G, ENST00000546844.1:c.1A>G, ENST00000547319.1:n.312A>G, ENST00000549111.5:n.97A>G, ENST00000551337.5:c.1A>G, ENST00000551988.5:n.90A>G, ENST00000553106.5:c.1A>G, ENST00000635500.1:n.29-4232A>G, NM_000277.2(PAH):c.1A>G (p.Met1Val)	CA114360


class ClinGen:
    ALLOWED_LABELS = ['variant_disease', 'variant_disease_gene']
    VARIANT_ID_MAPPING_PATH = './data_loading_support_files/clingen_variant_id_mapping.pkl'

    SOURCE = 'ClinGen'
    SOURCE_URL = 'https://search.clinicalgenome.org/kb/downloads'

    def __init__(self, filepath, label, dry_run=True, writer: Optional[Writer] = None):
        if label not in ClinGen.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(ClinGen.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.writer = writer

    def process_file(self):
        self.writer.open()
        self.load_variant_id_mapping()

        with open(self.filepath, 'r') as clingen_file:
            clingen_csv = csv.reader(clingen_file)
            next(clingen_csv)

            for row in clingen_csv:
                clinvar_id = row[0]
                # ignore those variants not in catalog
                if clinvar_id not in self.variant_id_mapping:
                    continue

                variant_id = self.variant_id_mapping[clinvar_id]

                gene_id = row[4]
                disease_id = row[6].replace(':', '_')  # MONDO id
                pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'

                variant_disease_id = hashlib.sha256(
                    '_'.join([variant_id, disease_id]).encode()).hexdigest()

                if self.label == 'variant_disease':
                    props = {
                        '_key': variant_disease_id,
                        '_from': 'variants/' + variant_id,
                        '_to': 'ontology_terms/' + disease_id,
                        'gene_id': 'genes/' + gene_id,
                        'assertion': row[9],
                        'pmids': [pmid_url + pmid for pmid in row[11].split(', ')],
                        'name': 'associated with',
                        'inverse_name': 'associated with',
                        'source': ClinGen.SOURCE,
                        'source_url': ClinGen.SOURCE_URL
                    }
                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

                elif self.label == 'variant_disease_gene':
                    variant_disease_gene_id = hashlib.sha256(
                        '_'.join([variant_disease_id, gene_id]).encode()).hexdigest()

                    props = {
                        '_key': variant_disease_gene_id,
                        '_from': 'variants_diseases/' + variant_disease_id,
                        '_to': 'genes/' + gene_id,
                        'name': 'associated with',
                        'inverse_name': 'associated with',
                        # gene-disease specific prop
                        'inheritance_mode': row[8],
                        'source': ClinGen.SOURCE,
                        'source_url': ClinGen.SOURCE_URL
                    }
                    self.writer.write(json.dumps(props))
                    self.writer.write('\n')

        self.writer.close()

    def load_variant_id_mapping(self):
        # key: ClinVar Variation Id; value: internal hashed variant id
        self.variant_id_mapping = {}
        with open(ClinGen.VARIANT_ID_MAPPING_PATH, 'rb') as mapfile:
            self.variant_id_mapping = pickle.load(mapfile)
