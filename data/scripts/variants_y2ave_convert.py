# Considering all y2ave variants loaded in a temporary collection using the FAVOR adapter.
# This script takes as an input the arangoexport output of this temporary collection: 'variants_y2ave.jsonl'

# The output for each chr contains the annotations that can be used to replace the initial FAVOR dataset.
# They can be loaded using arangoimp making sure '--on-duplicate update' is set.

import json

chrs_files = {
    'chr1': open('annotations_y2ave_chr1.jsonl', 'w+'),
    'chr2': open('annotations_y2ave_chr2.jsonl', 'w+'),
    'chr3': open('annotations_y2ave_chr3.jsonl', 'w+'),
    'chr4': open('annotations_y2ave_chr4.jsonl', 'w+'),
    'chr5': open('annotations_y2ave_chr5.jsonl', 'w+'),
    'chr6': open('annotations_y2ave_chr6.jsonl', 'w+'),
    'chr7': open('annotations_y2ave_chr7.jsonl', 'w+'),
    'chr8': open('annotations_y2ave_chr8.jsonl', 'w+'),
    'chr9': open('annotations_y2ave_chr9.jsonl', 'w+'),
    'chr10': open('annotations_y2ave_chr10.jsonl', 'w+'),
    'chr11': open('annotations_y2ave_chr11.jsonl', 'w+'),
    'chr12': open('annotations_y2ave_chr12.jsonl', 'w+'),
    'chr13': open('annotations_y2ave_chr13.jsonl', 'w+'),
    'chr14': open('annotations_y2ave_chr14.jsonl', 'w+'),
    'chr15': open('annotations_y2ave_chr15.jsonl', 'w+'),
    'chr16': open('annotations_y2ave_chr16.jsonl', 'w+'),
    'chr17': open('annotations_y2ave_chr17.jsonl', 'w+'),
    'chr18': open('annotations_y2ave_chr18.jsonl', 'w+'),
    'chr19': open('annotations_y2ave_chr19.jsonl', 'w+'),
    'chr20': open('annotations_y2ave_chr20.jsonl', 'w+'),
    'chr21': open('annotations_y2ave_chr21.jsonl', 'w+'),
    'chr22': open('annotations_y2ave_chr22.jsonl', 'w+'),
    'chrX': open('annotations_y2ave_chrX.jsonl', 'w+'),
    'chrY': open('annotations_y2ave_chrY.jsonl', 'w+')
}

with open('variants_y2ave.jsonl', 'r') as original:
    for line in original:
        orig_json = json.loads(line)

        annotations_keys = ['funseq_description', 'varinfo',  'vid', 'variant_vcf',  'variant_annovar', 'start_position',  'end_position', 'ref_annovar', 'alt_annovar', 'ref_vcf', 'alt_vcf', 'bravo_af', 'bravo_an', 'af_total', 'af_asj_female', 'af_eas_female', 'af_afr_male', 'af_female', 'af_fin_male', 'af_oth_female',
                            'af_ami', 'af_oth', 'af_male', 'af_ami_female', 'af_afr', 'af_eas_male', 'af_sas', 'af_nfe_female', 'af_asj_male', 'af_raw', 'af_oth_male', 'af_nfe_male', 'af_asj', 'af_amr_male', 'af_amr_female', 'af_sas_female', 'af_fin', 'af_afr_female', 'af_sas_male', 'af_amr', 'af_nfe', 'af_eas', 'af_ami_male', 'af_fin_female']

        annotations = {}
        for key in annotations_keys:
            if key in orig_json['annotations']:
                annotations[key] = orig_json['annotations'][key]

        if list(annotations.keys()) != ['varinfo']:
            processed_json = {
                '_key': orig_json['_key'],
                'chr': orig_json['chr'],
                'pos:long': orig_json['pos:long'],
                'ref': orig_json['ref'],
                'alt': orig_json['alt'],
                'spdi': orig_json['spdi'],
                'hgvs': orig_json['hgvs'],
                'variation_type': orig_json['variation_type'],
                'annotations': annotations,
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/',
                'y2ave': True
            }

            output_file = chrs_files[orig_json['chr']]
            output_file.write(json.dumps(processed_json))
            output_file.write('\n')

for chrr in chrs_files.keys():
    chrs_files[chrr].close()
