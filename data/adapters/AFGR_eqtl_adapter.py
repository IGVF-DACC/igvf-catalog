import csv
import gzip
import hashlib
import json
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import build_variant_id
from adapters.writer import Writer
from adapters.gene_validator import GeneValidator

# Example row from sorted.dist.hwe.af.AFR_META.eQTL.nominal.hg38a.txt.gz
# chr	snp_pos	snp_pos2	ref	alt	effect_af_eqtl	variant	feature	log10p	pvalue	beta	se	qstat	df	p_het	p_hwe	dist_start	dist_end	geneSymbol	geneType
# 1	16103	16103	T	G	0.0336427	1_16103_T_G	ENSG00000187583.10	0.1944867	0.6390183	0.242489	0.516955	NA	1.0	NA	1.000000	-950394	-959762	PLEKHN1	protein_coding


class AFGREQtl(BaseAdapter):
    ALLOWED_LABELS = ['AFGR_eqtl', 'AFGR_eqtl_term']
    SOURCE = 'AFGR'
    SOURCE_URL = 'https://github.com/smontgomlab/AFGR'
    BIOLOGICAL_CONTEXT = 'lymphoblastoid cell line'
    ONTOLOGY_TERM = 'EFO_0005292'  # lymphoblastoid cell line

    def __init__(self, filepath, label='AFGR_eqtl', writer: Optional[Writer] = None, validate=False, **kwargs):
        # Initialize base adapter first
        super().__init__(filepath, label, writer, validate)

        # Adapter-specific initialization
        self.gene_validator = GeneValidator()

    def _get_schema_type(self):
        """This adapter creates edges."""
        return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'AFGR_eqtl':
            return 'variants_genes'
        elif self.label == 'AFGR_eqtl_term':
            return 'variants_genes_terms'

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as qtl_file:
            qtl_csv = csv.reader(qtl_file, delimiter='\t')
            next(qtl_csv)

            for row in qtl_csv:
                chr, pos, ref, alt = row[6].split('_')

                # skipping deletions for now (can't be mapped to a spdi using current ga4gh lib)
                if alt == '*':
                    continue

                variant_id = build_variant_id(chr, pos, ref, alt, 'GRCh38')

                gene_id = row[7].split('.')[0]
                is_gene_id_valid = self.gene_validator.validate(gene_id)
                if not is_gene_id_valid:
                    continue

                variants_genes_id = hashlib.sha256(
                    (variant_id + '_' + gene_id + '_' + AFGREQtl.SOURCE).encode()).hexdigest()

                if self.label == 'AFGR_eqtl':
                    _id = variants_genes_id
                    _source = 'variants/' + variant_id
                    _target = 'genes/' + gene_id

                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'biological_context': AFGREQtl.BIOLOGICAL_CONTEXT,
                        'chr': 'chr' + chr,
                        # The three numeric values are not loaded as long data type somehow, though in schema it's labeled as int
                        # Manually changed data type from double to long in header file before importing into Arangodb
                        'log10pvalue': float(row[8]),  # MAX=616
                        'p_value': float(row[9]),
                        'effect_size': float(row[10]),
                        'label': 'eQTL',
                        'source': AFGREQtl.SOURCE,
                        'source_url': AFGREQtl.SOURCE_URL,
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'biological_process': 'ontology_terms/GO_0010468'
                    }

                elif self.label == 'AFGR_eqtl_term':
                    _id = hashlib.sha256(
                        (variants_genes_id + '_' + AFGREQtl.ONTOLOGY_TERM).encode()).hexdigest()
                    _source = 'variants_genes/' + variants_genes_id
                    _target = 'ontology_terms/' + AFGREQtl.ONTOLOGY_TERM
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'biological_context': AFGREQtl.BIOLOGICAL_CONTEXT,
                        'source': AFGREQtl.SOURCE,
                        'source_url': AFGREQtl.SOURCE_URL,
                        'name': 'occurs in',
                        'inverse_name': 'has measurement'
                    }

                if self.validate:
                    self.validate_doc(_props)

                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

        self.writer.close()
        self.gene_validator.log()
