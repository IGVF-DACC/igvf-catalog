import csv
import json
import os
import gzip
import requests
from adapters.file_fileset_adapter import FileFileSet
from adapters.helpers import bulk_check_caid_in_arangodb, CHR_MAP

from typing import Optional

from adapters.writer import Writer

# Example rows from maveDB file (IGVFFI0407TIWL.tsv.gz)
# variant_measurement_urn	score_set_urn	experiment_urn	clingen_allele_id	enst_id	ensp_id	score	assay_type	primary_publication_id	primary_publication_db  \
# score_range_1	score_range_1_name	score_range_1_classification	score_range_2	score_range_2_name	score_range_2_classification	score_range_3	score_range_3_name	score_range_3_classification	score_range_4	score_range_4_name	score_range_4_classificatioscore_range_5	score_range_5_name	score_range_5_classification	\
# experiment_title	experiment_short_description	experiment_abstract	experiment_methods	score_set_title	score_set_short_description	score_set_gene_symbols	score_set_abstract	score_set_methods
# urn:mavedb:00000001-c-1#1	urn:mavedb:00000001-c-1	urn:mavedb:00000001-c	CA2579769722	ENST00000356978.9		1.0297979489487	functional complementation	29269382	PubMed					Calmodulin yeast complementation	A Deep Mutational Scan of human Calmodulin using functional complementation in yeast.	Although we now routinely sequence human genomes, we can confidently identify only a fraction of the sequence variants that have a functional impact. Here, we developed a deep mutational scanning framework that produces exhaustive maps for human missense variants by combining random codon mutagenesis and multiplexed functional variation assays with computational imputation and refinement. We applied this framework to four proteins corresponding to six human genes: UBE2I (encoding SUMO E2 conjugase), SUMO1 (small ubiquitin-like modifier), TPK1 (thiamin pyrophosphokinase), and CALM1/2/3 (three genes encoding the protein calmodulin). \
# The resulting maps recapitulate known protein features and confidently identify pathogenic variation. Assays potentially amenable to deep mutational scanning are already available for 57% of human disease genes, suggesting that DMS could ultimately map functional variation for all human disease genes.	A Deep Mutational Scan of Calmodulin (*CALM1*) using functional complementation in yeast was performed using DMS-TileSeq and a machine-learning method was used to impute the effects of missing variants and refine measurements of lower confidence. See [**Weile *et al.* 2017**](http://msb.embopress.org/content/13/12/957) for details.	Human Calmodulin DMS-TileSeq	A Deep Mutational Scan of human Calmodulin using functional complementation in yeast via DMS-TileSeq.	CALM1,CALM2,CALM3	"Although we now routinely sequence human genomes, we can confidently identify only a fraction of the sequence variants that have a functional impact. \
# Here, we developed a deep mutational scanning framework that produces exhaustive maps for human missense variants by combining random codon mutagenesis and multiplexed functional variation assays with computational imputation and refinement. We applied this framework to four proteins corresponding to six human genes: UBE2I (encoding SUMO E2 conjugase), SUMO1 (small ubiquitin-like modifier), TPK1 (thiamin pyrophosphokinase), and CALM1/2/3 (three genes encoding the protein calmodulin). The resulting maps recapitulate known protein features and confidently identify pathogenic variation. Assays potentially amenable to deep mutational scanning are already available for 57% of human disease genes, suggesting that DMS could ultimately map functional variation for all human disease genes.

# All fields are text (enum), except for score (float).
# clingen_allele_ids: Comma-separated list of ClinGen allele IDs. score_set_urn + clingen_allele_id together form a unique identifier for the row, as an alternative to variant_urn.


class MAVEDB:
    ALLOWED_LABELS = ['variants_phenotypes',
                      'variants_phenotypes_coding_variants']
    SOURCE = 'IGVF'
    EDGE_NAME = 'mutational effect'
    EDGE_INVERSE_NAME = 'altered due to mutation'
    FLOAT_FIELDS = ['score']
    SKIP_FIELDS = ['clingen_allele_id']  # already in variants
    RENAME_FIELDS = {
        'enst_id': 'transcript_id',
        'ensp_id': 'protein_id'
    }
    ASSAY_TYPE_TO_PHENOTYPE = {
        'functional complementation': 'GO_0003674',
        'other': 'GO_0003674',
        'SGE': 'NCIT_C16407',
        'VAMP-seq': 'OBA_0000128'
    }
    CHUNK_SIZE = 5000

    def __init__(self, filepath, label='variants_phenotypes', writer: Optional[Writer] = None, **kwargs):
        if label not in MAVEDB.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(MAVEDB.ALLOWED_LABELS))

        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.label = label
        self.writer = writer
        self.files_filesets = FileFileSet(self.file_accession)

    def process_variants_phenotypes_chunk(self, chunk):
        caids = []
        for row in chunk:
            caids.extend(row[3].split(','))
#        print('querying caids...')
        mapped_caids = bulk_check_caid_in_arangodb(list(set(caids)))
        skipped_caids = set()
        for row in chunk:
            for variant_id in row[3].split(','):
                if variant_id not in mapped_caids:
                    skipped_caids.add(variant_id)
                else:
                    if len(mapped_caids[variant_id]) > 1:
                        mapped_caids_str = ','.join(mapped_caids)
                        print(
                            f'WARNING: {variant_id} mapped to multiple variants: {mapped_caids_str}')
                    for variant_key in mapped_caids[variant_id]:
                        # score_set_urn + clingen_allele_id together form a unique identifier for the row
                        edge_key = variant_key + '_' + \
                            row[1] + '_' + self.file_accession
                        _props = {
                            '_key': edge_key,
                            '_from': 'variants/' + variant_key,
                            '_to': 'ontology_terms/' + self.ASSAY_TYPE_TO_PHENOTYPE[row[7].strip()],
                            'source': self.SOURCE,
                            'source_url': self.source_url,
                            'name': self.EDGE_NAME,
                            'inverse_name': self.EDGE_INVERSE_NAME,
                            # not currently supported for curated set
                            'files_filesets': 'files_filesets/' + self.file_accession,
                            'method': 'maveDB'  # hard code here
                        }

                        for i, value in enumerate(row):
                            field = self.header[i]
                            if field in self.SKIP_FIELDS:
                                continue
                            if field in self.FLOAT_FIELDS:
                                value = float(value) if value else None
                            elif not value:  # empty str
                                value = None
                            else:
                                value = value.strip()
                            if field in self.RENAME_FIELDS:
                                field = self.RENAME_FIELDS[field]
                            _props.update({field: value})
                        print(variant_id + '\t' + mapped_caids[variant_id][0])
                        self.writer.write(json.dumps(_props) + '\n')
        if skipped_caids:
            with open(f'./skipped_variants_{self.file_accession}.txt', 'a') as skipped_list:
                for skipped in list(skipped_caids):
                    skipped_list.write(skipped + '\n')

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')
            self.header = next(reader)
            chunk = []

            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % self.CHUNK_SIZE == 0:
                    if self.label == 'variants_phenotypes':
                        self.process_variants_phenotypes_chunk(chunk)

                    chunk = []

        if chunk:
            if self.label == 'variants_phenotypes':
                self.process_variants_phenotypes_chunk(chunk)

        self.writer.close()
