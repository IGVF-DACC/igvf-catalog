import os
import gzip
import json
import hashlib

from adapters import Adapter
from db.arango_db import ArangoDB

# Input file from:
# https://www.informatics.jax.org/downloads/reports/MGI_QTLAllele.rpt

#
# Allele symbols are usually of the form xxx<yy>, where the <> enclose the part of the symbol that is superscripted.
#
# Transgene insertions, with symbols of the form Tg(aaa)##bbb, are included in this listing, but notably have no corresponding gene marker.
#
# For details of nomenclature rules, see http://www.informatics.jax.org/mgihome/nomen/index.shtml
#
# MGI:5823894	Aaaq1<129S6/SvEvTac>	129S6/SvEvTac	QTL	20133902	MGI:5823834	Aaaq1			1	126495943	126495943	GRCm39
# MGI:5823908	Aaaq1<C57BL/6J>	C57BL/6J	QTL	20133902	MGI:5823834	Aaaq1			1	126495943	126495943	GRCm39
# MGI:3042398	Aabpr<NZB/Slc>	NZB/Slc	QTL	14695357	MGI:3042396	Aabpr			2	116033229	122207534	GRCm39	MP:0005384,MP:0005387,MP:0005397
# MGI:3042399	Aabpr<NZW/Slc>	NZW/Slc	QTL	14695357	MGI:3042396	Aabpr			2	116033229	122207534	GRCm39
# MGI:2155901	Aaiq1<A/J>	A/J	QTL		MGI:1196361	Aaiq1			null	null	null	null

# Headers:
# 'MGI Allele Accession ID'
# 'Allele Symbol'
# 'Allele Name'
# 'Allele Type'
# 'PubMed ID for original reference'
# 'MGI Marker Accession ID'
# 'Marker Symbol'
# 'Marker RefSeq ID'
# 'Marker Ensembl ID'
# 'Marker Chromosome'
# 'Marker Start Coordinate'
# 'Marker End Coordinate'
# 'Genome Build'
# 'High-level Mammalian Phenotype ID (comma-delimited)'


class MGIQtlAdapter(Adapter):
    def __init__(self, filepath):
        self.filepath = filepath
        self.label = 'mm_qtls'

        super(MGIQtlAdapter, self).__init__()

    def process_file(self):
        genes = set()

        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue

            data_line = line.strip().split('\t')

            id = data_line[0] + '_' + data_line[5]
            label = 'mm_qtls'
            _from = data_line[0]
            _to = data_line[5]

            props = {
                'mgi_allele_accession_id': data_line[0],
                'allele_symbol': data_line[1],
                'allele_name': data_line[2],
                'allele_type': data_line[3],
                'pubmed_id': data_line[4],
                'marker_mgi_id': data_line[5],
                'marker_symbol': data_line[6],
                'maker_refseq_id': data_line[7],
                'marker_ensembl_id': data_line[8],
                'marker_chr': data_line[9],
                'marker_start': data_line[10],
                'marker_end': data_line[11],
                'genome_build': data_line[12],
                'phenotype_id': None if len(data_line) < 14 else data_line[13],
                'source': 'MGI',
                'source_url': 'https://www.informatics.jax.org/downloads/reports/MGI_QTLAllele.rpt'
            }

            if data_line[9] == 'null' or data_line[10] == 'null' or data_line[11] == 'null' or data_line[12] == 'null':
                continue

            genes.add(data_line[5])

            yield(id, _from, _to, label, props)

        import pdb
        pdb.set_trace()
