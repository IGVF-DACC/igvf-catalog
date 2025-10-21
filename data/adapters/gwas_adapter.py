import json
import hashlib
import pickle
from math import log10
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError
from schemas.registry import get_schema
from adapters.helpers import build_variant_id
from adapters.writer import Writer


# GWAS variant to phenotype - v2d_igvf.tsv
# variant_id      mondo_id        efo_id  study_id        lead_chrom      lead_pos        lead_ref        lead_alt        direction       beta    beta_ci_lower   beta_ci_upper   odds_ratio      oddsr_ci_lower  oddsr_ci_upper        pval_mantissa   pval_exponent   pval    ancestry_initial        ancestry_replication    n_cases n_initial       n_replication   pmid    pub_author      pub_date        pub_journal     pub_title             has_sumstats    num_assoc_loci  source  trait_reported  trait_efos      trait_category  tag_chrom       tag_pos tag_ref tag_alt overall_r2      pics_95perc_credset     AFR_1000G_prop  AMR_1000G_prop  EAS_1000G_prop        EUR_1000G_prop  SAS_1000G_prop  log10_ABF       posterior_prob
# 1:1010747:GT:G  NA      EFO_0007010     NEALE2_20003_1140867876 1       1010747 GT      G       -                               0.3464239658215028      0.2372663081628671      0.5058011186869372      4.02417 -8            4.02417e-08     ['European=361141']     []      491.0   361141  0.0             UKB Neale v2    2018-08-01                      True    6       NEALE   Prozac 20mg capsule | treatment/medication code ['EFO_0007010']       measurement     1       988598  A       AG      0.551468126881  True    0.0     0.0     0.0     1.0     0.0     5.112385010047364       0.004867160933888
# 1:1009731:C:T   NA      EFO_0007937     GCST90087821    1       1009731 C       T       +       0.707278        0.5564011777996241      0.8581548222003759                              4.0     -20     4e-20   ['European=5366']     []              5366            PMID:35078996   Gudjonsson A    2022-01-25      Nat Commun      A genome-wide association study of serum proteins reveals shared loci with common diseases.     False         2       GCST    Serum levels of protein ISG15   ['EFO_0007937'] measurement     1       988598  A       AG      0.803520410449  True    0.0     0.0     0.0     1.0     0.0
# 1:1008088:T:C   NA      EFO_0007937     GCST006585_950  1       1008088 T       C       +       0.73554206      0.5305998818099342      0.9404842381900658                              2.0     -12     2e-12   ['European=3200']     []              3200            PMID:30072576   Emilsson V      2018-08-02      Science Co-regulatory networks of human serum proteins link genetics to disease.        False   1       GCST    Blood protein levels [ISG15, 14151_4_3]       ['EFO_0007937'] measurement     1       988598  A       AG      0.825908352025  True    0.0     0.0     0.0     1.0     0.0


# GWAS variant to gene - scored file (v2g_scored_igvf):
# (note: v2g_igvf has the same columns except for the last 4)
# variant_id      gene_id chr_id  position        ref_allele      alt_allele      feature type_id source_id          fpred_labels    fpred_scores    fpred_max_label fpred_max_score qtl_beta        qtl_se  qtl_pval           qtl_score       interval_score  qtl_score_q     interval_score_q        d       distance_score  distance_score_q   overall_score   source_list     source_score_list
# 5:141242639:G:T ENSG00000204961 5       141242639       G       T       MACROPHAGES_M0  pchic   javierre2016       []      []                                                      8.56622816615577                0.7                                0.0663983903420523      ['canonical_tss' 'javierre2016']        [0.2 0.8]
# 5:141242639:G:T ENSG00000204961 5       141242639       G       T       MACROPHAGES_M1  pchic   javierre2016       []      []                                                      9.03867857946432                0.7                                0.0663983903420523      ['canonical_tss' 'javierre2016']        [0.2 0.8]
# 5:141242736:GT:G        ENSG00000253953 5       141242736       GT      G       unspecified     distance           canonical_tss   []      []                                                                                 144962.0        6.898359570094232e-06   0.7     0.0929577464788732      ['canonical_tss' 'javierre2016']   [0.7 0.7]

# Important! We need to handle the case where breaklines happen in the middle of certain lines, like:
# 6:32387828:G:A	ENSG00000237541	6	32387828	G	A	ROSMAP-BRAIN_NAIVE	eqtl	eqtl	[]	[]			0.364989	0.0521153	7.24831e-12	11.139763240771314		0.6					0.4462776659959758	"['sqtl' 'pqtl' 'javierre2016' 'thurman2012' 'jung2019' 'canonical_tss'
# 'eqtl']"	[0.7 0.9 0.7 0.  0.  0.3 0.9]


class GWAS:
    # studies, variants <-(edge)-> phenotypes, edge <-> studies (hyperedge with variant info & study-specific stats)
    # variants in GWAS is 1-based, need to convert gwas variant position from 1-based to 0-based

    MAX_LOG10_PVALUE = 27000  # max abs value on pval_exponent is 26677
    ONTOLOGY_MAPPING_PATH = './data_loading_support_files/gwas_ontology_term_name_mapping.pkl'

    ALLOWED_COLLECTIONS = ['studies',
                           'variants_phenotypes', 'variants_phenotypes_studies']
    SOURCE_URL = 'https://api.data.igvf.org/reference-files/IGVFFI1309WDQG'

    def __init__(self, variants_to_ontology, gwas_collection='studies', dry_run=True, writer: Optional[Writer] = None, validate=False, **kwargs):
        if gwas_collection not in GWAS.ALLOWED_COLLECTIONS:
            raise ValueError('Invalid collection. Allowed values: ' +
                             ','.join(GWAS.ALLOWED_COLLECTIONS))

        self.variants_to_ontology_filepath = variants_to_ontology

        self.type = 'edge'
        self.dataset = gwas_collection
        self.label = gwas_collection

        if gwas_collection == 'studies':
            self.type = 'node'
        self.processed_keys = set()

        self.gwas_collection = gwas_collection

        self.dry_run = dry_run
        self.writer = writer
        self.validate = validate
        if self.validate:
            if self.gwas_collection == 'studies':
                self.schema = get_schema(
                    'nodes', 'studies', self.__class__.__name__)
            elif self.gwas_collection == 'variants_phenotypes':
                self.schema = get_schema(
                    'edges', 'variants_phenotypes', self.__class__.__name__)
            elif self.gwas_collection == 'variants_phenotypes_studies':
                self.schema = get_schema(
                    'edges', 'variants_phenotypes_studies', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(
                f'Document validation failed: {e.message} doc: {doc}')

    # trying to capture the breakline problem described in the comments above
    def line_appears_broken(self, row):
        return row[-1].startswith('"[') and not row[-1].endswith(']"')

    def studies_variants_key(self, row):
        variant_id = build_variant_id(row[4], row[5], row[6], row[7])
        study_id = row[3]

        return hashlib.sha256((variant_id + '_' + study_id).encode()).hexdigest()

    def process_studies(self, row):
        study_id = row[3]

        if study_id in self.processed_keys:
            return None
        self.processed_keys.add(study_id)

        props = {
            '_key': study_id,
            'name': study_id,
            'ancestry_initial': row[18],
            'ancestry_replication': row[19],
            'n_cases': row[20],
            'n_initial': row[21],
            'n_replication': row[22],
            'pmid': row[23],
            'pub_author': row[24],
            'pub_date': row[25],
            'pub_journal': row[26],
            'pub_title': row[27],
            'has_sumstats': row[28],
            'num_assoc_loci': row[29],
            'study_source': row[30],
            'trait_reported': row[31],
            'trait_efos': row[32],
            'trait_category': row[33],
            'source': 'OpenTargets',
            'version': 'October 2022 (22.10)',
            'source_url': self.SOURCE_URL
        }
        return props

    def process_variants_phenotypes_studies(self, row, edge_key, phenotype_id, tagged_variants):
        study_id = row[3]
        studies_variants_key = self.studies_variants_key(
            row)  # key used for tagged_variants

        key = hashlib.sha256(
            # combination of variant_id + phenotype_id + study_id
            (edge_key + '_' + study_id).encode()).hexdigest()

        if key in self.processed_keys:
            return None
        self.processed_keys.add(key)

        pvalue = float(row[17] or 0)
        if pvalue == 0:
            log_pvalue = GWAS.MAX_LOG10_PVALUE  # Max value based on data
        else:
            log_pvalue = -1 * log10(pvalue)

        return {
            '_to': 'studies/' + study_id,
            '_from': 'variants_phenotypes/' + edge_key,
            '_key': key,
            'lead_chrom': row[4],
            'lead_pos': int(row[5]) - 1,
            'lead_ref': row[6],
            'lead_alt': row[7],
            'phenotype_term': self.ontology_name_mapping.get(phenotype_id),
            'direction': row[8],
            'beta': float(row[9] or 0),
            'beta_ci_lower': float(row[10] or 0),
            'beta_ci_upper': float(row[11] or 0),
            'odds_ratio': float(row[12] or 0),
            'oddsr_ci_lower': float(row[13] or 0),
            'oddsr_ci_upper': float(row[14] or 0),
            'p_val_mantissa': float(row[15] or 0),
            'p_val_exponent': float(row[16] or 0),
            'p_val': pvalue,
            'log10pvalue': log_pvalue,
            'tagged_variants': tagged_variants[studies_variants_key],
            'source': 'OpenTargets',
            'version': 'October 2022 (22.10)',
            'name': 'collected in',
            'inverse_name': 'collects'
        }

    def process_variants_phenotypes(self, row):
        variant_id = build_variant_id(row[4], row[5], row[6], row[7])

        ontology_term_id = 'ontology_terms/'

        equivalent_term_id = None
        # give preference to MONDO if defined, otherwise, use EFO term
        if row[1] != 'NA':
            ontology_term_id = ontology_term_id + row[1]
            equivalent_term_id = 'ontology_terms/' + row[2]
        else:
            ontology_term_id = ontology_term_id + row[2]

        # MANY records have no ontology term. Ignoring those lines.
        if ontology_term_id == 'ontology_terms/':
            return None

        key = hashlib.sha256(
            (variant_id + '_' + ontology_term_id).encode()).hexdigest()

        if self.gwas_collection == 'variants_phenotypes':
            if key in self.processed_keys:
                return None
            self.processed_keys.add(key)

        return {
            '_from': 'variants/' + variant_id,
            '_to': ontology_term_id,
            '_key': key,
            'equivalent_ontology_term': equivalent_term_id,
            'source': 'OpenTargets',
            'version': 'October 2022 (22.10)',
            'name': 'associated with',
            'inverse_name': 'associated with'
        }

    def process_file(self):
        self.writer.open()
        # tagged variants & genes info go to heyperedge collection
        if self.gwas_collection == 'variants_phenotypes_studies':
            print('Collecting tagged variants...')
            tagged = self.get_tagged_variants()

            # mapping from ontology id to name for phenotypes
            self.load_ontology_name_mapping()
        header = None
        trying_to_complete_line = None

        # Many records are duplicated with different tagged variants.
        # We are collecting all tagged variants at once.
        # For that, we need to keep track of which keys we already processed to avoid duplicated entries.
        print('Processing file...')

        for record in open(self.variants_to_ontology_filepath, 'r'):
            if header is None:
                header = record.strip().split('\t')
                continue

            if trying_to_complete_line:
                record = trying_to_complete_line + record
                trying_to_complete_line = None

            row = record.strip().split('\t')

            if self.line_appears_broken(row):
                trying_to_complete_line = record
                continue

            # many rows have incomplete empty columns
            row = row + [None] * (len(header) - len(row))

            props = None

            if self.gwas_collection == 'studies':
                props = self.process_studies(row)
            elif self.gwas_collection == 'variants_phenotypes':
                props = self.process_variants_phenotypes(row)
            elif self.gwas_collection == 'variants_phenotypes_studies':
                edge_props = self.process_variants_phenotypes(row)
                if edge_props is None:
                    continue
                else:
                    # i.e. the _from key in this hyperedge collection
                    edge_key = edge_props['_key']
                    phenotype_id = edge_props['_to'].split('/')[1]
                    props = self.process_variants_phenotypes_studies(
                        row, edge_key, phenotype_id, tagged)
            if props is None:
                continue
            if self.validate:
                self.validate_doc(props)
            self.writer.write(json.dumps(props))
            self.writer.write('\n')

        self.writer.close()

    def get_tagged_variants(self):
        header = None
        trying_to_complete_line = None
        tagged_variants = {}

        for record in open(self.variants_to_ontology_filepath, 'r'):
            if header is None:
                header = record.strip().split('\t')
                continue

            if trying_to_complete_line:
                record = trying_to_complete_line + record
                trying_to_complete_line = None

            row = record.strip().split('\t')

            if self.line_appears_broken(row):
                trying_to_complete_line = record
                continue

            # grouping tagged variants by main variant + study
            key = self.studies_variants_key(row)

            # a few rows are incomplete. Filling empty values with None
            row = row + [None] * (len(header) - len(row))

            variant = {
                'tag_chrom': row[34],
                'tag_pos': int(row[35]) - 1,
                'tag_ref': row[36],
                'tag_alt': row[37],
                'overall_r2': row[38],
                'pics_95perc_credset': row[39],
                'AFR_1000G_prop': row[40],
                'AMR_1000G_prop': row[41],
                'EAS_1000G_prop': row[42],
                'EUR_1000G_prop': row[43],
                'SAS_1000G_prop': row[44],
                'log10_ABF': row[45],
                'posterior_prob': row[46]
            }

            if key not in tagged_variants:
                tagged_variants[key] = [variant]
            else:
                should_add = True
                for tagged in tagged_variants[key]:
                    if tagged == variant:
                        should_add = False
                        break
                if should_add:
                    tagged_variants[key].append(variant)

        return tagged_variants

    def load_ontology_name_mapping(self):
        # mapping from ontology id to ontology name for phenotypes
        self.ontology_name_mapping = {}
        with open(GWAS.ONTOLOGY_MAPPING_PATH, 'rb') as mapfile:
            self.ontology_name_mapping = pickle.load(mapfile)
