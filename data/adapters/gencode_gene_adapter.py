import gzip
import json
from typing import Optional

from adapters.writer import Writer
import requests

# Example genocde gtf input file:
# ##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)
# ##provider: GENCODE
# ##contact: gencode-help@ebi.ac.uk
# ##format: gtf
# ##date: 2022-11-29
# chr1	HAVANA	gene	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; gene_type "lncRNA"; gene_name "DDX11L2"; level 2; tag "overlaps_pseudogene";
# chr1	HAVANA	transcript	11869	14409	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	11869	12227	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 1; exon_id "ENSE00002234944.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";
# chr1	HAVANA	exon	12613	12721	.	+	.	gene_id "ENSG00000290825.1"; transcript_id "ENST00000456328.2"; gene_type "lncRNA"; gene_name "DDX11L2"; transcript_type "lncRNA"; transcript_name "DDX11L2-202"; exon_number 2; exon_id "ENSE00003582793.1"; level 2; transcript_support_level "1"; tag "basic"; tag "Ensembl_canonical"; havana_transcript "OTTHUMT00000362751.1";


class GencodeGene:
    ALLOWED_KEYS = ['gene_id', 'gene_type', 'gene_name',
                    'transcript_id', 'transcript_type', 'transcript_name', 'hgnc_id', 'mgi_id']
    INDEX = {'chr': 0, 'type': 2, 'coord_start': 3, 'coord_end': 4, 'info': 8}
    ALLOWED_LABELS = [
        'gencode_gene',
        'mm_gencode_gene',
    ]
    ALLOWED_MODE = [
        # output a jsonl file for loading genes into igvfd (without the collections and study_sets properties)
        'igvfd'
        # output a jsonl file with the same properties as on igvfd (from gencode gtf file), also load collections and study_sets properties from igvfd portal
        'catalog'
    ]
    # TODO: add this arg data_parser

    def __init__(self, filepath=None, gene_alias_file_path=None, chr='all', label='gencode_gene', mode='catalog', dry_run=False, writer: Optional[Writer] = None, **kwargs):
        if label not in GencodeGene.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(GencodeGene.ALLOWED_LABELS))
        if mode not in GencodeGene.ALLOWED_MODE:
            raise ValueError('Invalid mode. Allowed values: ' +
                             ','.join(GencodeGene.ALLOWED_MODE))

        self.filepath = filepath
        self.chr = chr
        self.label = label
        self.gene_alias_file_path = gene_alias_file_path
        self.writer = writer
        self.dry_run = dry_run
        self.mode = mode
        if self.label == 'gencode_gene':
            self.version = 'v43'
            self.source_url = 'https://www.gencodegenes.org/human/'
            self.organism = 'Homo sapiens'
        else:
            self.version = 'vM33'
            self.source_url = 'https://www.gencodegenes.org/mouse/'
            self.organism = 'Mus musculus'

    def parse_info_metadata(self, info):
        parsed_info = {}
        for key, value in zip(info, info[1:]):
            if key in GencodeGene.ALLOWED_KEYS:
                parsed_info[key] = value.replace('"', '').replace(';', '')
        return parsed_info

    # the gene alias dict will use both ensembl id and hgnc id (or mgi id for mouse) as key
    def get_collection_alias(self):
        alias_dict = {}
        with gzip.open(self.gene_alias_file_path, 'rt') as input:
            next(input)
            for line in input:
                hgnc = ''
                ensembl = ''
                mgi = ''
                (tax_id, gene_id, symbol, locus_tag, synonyms, dbxrefs, chromosome, map_location, description, type_of_gene, symbol_from_nomenclature_authority,
                 full_name_from_nomenclature_authority, Nomenclature_status, Other_designations, Modification_date, Feature_type) = line.split('\t')
                split_dbxrefs = dbxrefs.split('|')
                for ref in split_dbxrefs:
                    if ref.startswith('HGNC:'):
                        hgnc = ref[5:]
                    elif ref.startswith('Ensembl:'):
                        ensembl = ref[8:]
                    elif ref.startswith('MGI:'):
                        mgi = ref[4:]
                if ensembl or hgnc or mgi:
                    complete_synonyms = []
                    complete_synonyms.append(symbol)
                    for i in synonyms.split('|'):
                        complete_synonyms.append(i)
                    for i in Other_designations.split('|'):
                        complete_synonyms.append(i)
                    complete_synonyms.append(
                        symbol_from_nomenclature_authority)
                    complete_synonyms.append(
                        full_name_from_nomenclature_authority)
                    complete_synonyms = list(set(complete_synonyms))
                    if '-' in complete_synonyms:
                        complete_synonyms.remove('-')
                    alias = {
                        'alias': complete_synonyms,
                        'entrez': gene_id
                    }
                    if self.label == 'gencode_gene' and hgnc:
                        alias.update(
                            {'hgnc': hgnc}
                        )
                        alias_dict[hgnc] = alias
                    if self.label == 'mm_gencode_gene' and mgi:
                        alias.update(
                            {'mgi': mgi}
                        )
                        alias_dict[mgi] = alias
                    if ensembl:
                        alias_dict[ensembl] = alias
        return alias_dict

    def get_hgnc_id(self, id, info, alias_dict):
        hgnc_id = info.get('hgnc_id')
        if not hgnc_id:
            alias = alias_dict.get(id)
            if alias:
                hgnc_id = alias.get('hgnc')
        return hgnc_id

    def get_mgi_id(self, id, info, alias_dict):
        mgi_id = info.get('mgi_id')
        if not mgi_id:
            alias = alias_dict.get(id)
            if alias:
                mgi_id = alias.get('mgi')
        return mgi_id

    def get_alias_by_id(self, id, hgnc_id, mgi_id, alias_dict):
        for key in [id, hgnc_id, mgi_id]:
            if key in alias_dict:
                return alias_dict[key]
        return None

    def get_entrez_id(self, alias):
        for item in alias:
            if item.startswith('ENTREZ:'):
                return item

    def get_additional_props_from_igvfd(self, id):
        igvfd_props = {}
        igvfd_url = 'https://api.data.igvf.org/'
        gene_object = requests.get(
            igvfd_url + id + '/@@object?format=json').json()

        igvfd_props['collections'] = gene_object.get('collections')
        igvfd_props['study_sets'] = gene_object.get('study_sets')
        return igvfd_props

    def process_file(self):
        alias_dict = self.get_collection_alias()
        self.writer.open()
        for line in open(self.filepath, 'r'):
            if line.startswith('#'):
                continue
            split_line = line.strip().split()
            if split_line[GencodeGene.INDEX['type']] == 'gene':
                info = self.parse_info_metadata(
                    split_line[GencodeGene.INDEX['info']:])
                gene_id = info['gene_id']
                id = gene_id.split('.')[0]
                hgnc_id = self.get_hgnc_id(id, info, alias_dict)
                mgi_id = self.get_mgi_id(id, info, alias_dict)
                alias = self.get_alias_by_id(id, hgnc_id, mgi_id, alias_dict)
                if gene_id.endswith('_PAR_Y'):
                    id = id + '_PAR_Y'
                to_json = {
                    '_key': id,
                    'gene_id': gene_id,
                    'gene_type': info['gene_type'],
                    'chr': split_line[GencodeGene.INDEX['chr']],
                    # the gtf file format is [1-based,1-based], needs to convert to BED format [0-based,1-based]
                    'start': int(split_line[GencodeGene.INDEX['coord_start']]) - 1,
                    'end': int(split_line[GencodeGene.INDEX['coord_end']]),
                    'gene_symbol': info['gene_name'],  # change or keep both?
                    # add ENST, ENSP?
                    'name': info['gene_name'],
                    'source': 'GENCODE',
                    'version': self.version,
                    'source_url': self.source_url,
                    'organism': self.organism
                }
                if hgnc_id:
                    to_json.update(
                        {
                            'hgnc': hgnc_id,
                        }
                    )
                if mgi_id:
                    to_json.update(
                        {
                            'mgi': mgi_id,
                        }
                    )
                if alias:
                    to_json.update(
                        {
                            # use the same prop name (synonyms) as igvfd
                            'synonyms': alias['alias'],
                            'entrez': alias['entrez']
                        }
                    )
                if self.mode == 'catalog':  # load collections and study_sets from igvfd portal
                    igvfd_props = self.get_additional_props_from_igvfd(id)
                    # For genes without those properties, is None or empty list better for loading? (load as None right now)
                    to_json.update(igvfd_props)
                self.writer.write(json.dumps(to_json))
                self.writer.write('\n')
        self.writer.close()
