drugs_variants = {
    '/drugs/variants': [{
        'params': {
            'drug_id': 'PA448497',
            'drug_name': 'aspirin',
            'pmid': '20824505',
            'phenotype_categories': 'Toxicity',
            'verbose': 'false'
        },
        'response': [
            {
                'drug': 'drugs/PA448497',
                'sequence variant': 'variants/b8d8a33facd5b62cb7f1004ae38419b8d914082ea9b217bef008a6a7f0218687',
                'gene_symbol': [
                    'AGT'
                ],
                'pmid': '20824505',
                'study_parameters': [
                    {
                        'study_parameter_id': '1009568432',
                        'study_type': 'cohort',
                        'study_cases': '68',
                        'study_controls': '357',
                        'p-value': '< 0.05',
                        'biogeographical_groups': 'East Asian'
                    }
                ],
                'phenotype_categories': [
                    'Toxicity'
                ],
                'source': 'pharmGKB',
                'source_url': 'https://www.pharmgkb.org/variantAnnotation/1009360953'
            }
        ]
    }, {
        'params': {
            'drug_id': 'PA448497',
            'drug_name': 'aspirin',
            'pmid': '20824505',
            'phenotype_categories': 'Toxicity',
            'verbose': 'true'
        },
        'response': [
            {
                'drug': 'drugs/PA448497',
                'sequence variant': {
                    '_id': 'b8d8a33facd5b62cb7f1004ae38419b8d914082ea9b217bef008a6a7f0218687',
                    'chr': 'chr1',
                    'pos': 230714139,
                    'rsid': [
                        'rs5050'
                    ],
                    'ref': 'T',
                    'alt': 'G',
                    'spdi': 'NC_000001.11:230714139:T:G',
                    'hgvs': 'NC_000001.11:g.230714140T>G',
                    'qual': '.',
                    'filter': None,
                    'annotations': {
                        'freq': {
                            '1000genomes': {
                                'ref:long': 0.8241,
                                'alt:long': 0
                            },
                            'alspac': {
                                'ref:long': 0.8441,
                                'alt:long': 0
                            },
                            'estonian': {
                                'ref:long': 0.8107,
                                'alt:long': 0
                            },
                            'genome_dk': {
                                'ref:long': 0.85,
                                'alt:long': 0
                            },
                            'gonl': {
                                'ref:long': 0.8377,
                                'alt:long': 0
                            },
                            'hgdp_stanford': {
                                'ref:long': 0.8272,
                                'alt:long': 0
                            },
                            'hapmap': {
                                'ref:long': 0.84,
                                'alt:long': 0
                            },
                            'korean': {
                                'ref:long': 0.8164,
                                'alt:long': 0
                            },
                            'northernsweden': {
                                'ref:long': 0.8433,
                                'alt:long': 0
                            },
                            'page_study': {
                                'ref:long': 0.8311,
                                'alt:long': 0
                            },
                            'prjeb36033': {
                                'ref:long': 0.8857,
                                'alt:long': 0
                            },
                            'pharmgkb': {
                                'ref:long': 0.883,
                                'alt:long': 0
                            },
                            'qatari': {
                                'ref:long': 0.8796,
                                'alt:long': 0
                            },
                            'sgdp_prj': {
                                'ref:long': 0.4595,
                                'alt:long': 0.006757
                            },
                            'siberian': {
                                'ref:long': 0.3571,
                                'alt:long': 0
                            },
                            'tommo': {
                                'ref:long': 0.7589,
                                'alt:long': 0
                            },
                            'topmed': {
                                'ref:long': 0.8342,
                                'alt:long': 0
                            },
                            'twinsuk': {
                                'ref:long': 0.836,
                                'alt:long': 0
                            },
                            'dbgap_popfreq': {
                                'ref:long': 0.8768,
                                'alt:long': 0
                            }
                        },
                        'varinfo': '1-230714140-T-G',
                        'vid': '6.36746e+08',
                        'variant_vcf': '1-230714140-T-G',
                        'variant_annovar': '1-230714140-230714140-T-G',
                        'start_position': '2.30714e+08',
                        'end_position': '2.30714e+08',
                        'ref_annovar': 'T',
                        'alt_annovar': 'G',
                        'ref_vcf': 'T',
                        'alt_vcf': 'G',
                        'apc_conservation': 2.37719,
                        'apc_conservation_v2': 4.1684,
                        'apc_epigenetics_active': 19.8025,
                        'apc_epigenetics': 20.9484,
                        'apc_epigenetics_repressed': 3.93328,
                        'apc_epigenetics_transcription': 2.35907,
                        'apc_local_nucleotide_diversity': 1.30443,
                        'apc_local_nucleotide_diversity_v2': 0.177866,
                        'apc_local_nucleotide_diversity_v3': 0.16922,
                        'apc_mappability': 17.0936,
                        'apc_micro_rna': 99.4512,
                        'apc_mutation_density': 0.183242,
                        'apc_protein_function': 20.2494,
                        'apc_protein_function_v2': 4.92793e-10,
                        'apc_protein_function_v3': 2.96949,
                        'apc_proximity_to_coding': 10.3211,
                        'apc_proximity_to_coding_v2': 15.1786,
                        'apc_proximity_to_tsstes': 14.2933,
                        'apc_transcription_factor': 21.409,
                        'bravo_an': '264690',
                        'bravo_af': '0.165779',
                        'filter_status': 'PASS',
                        'origin': None,
                        'fathmm_xf': '6.60508',
                        'funseq_description': 'noncoding',
                        'af_total': 0.168579,
                        'af_asj_female': 0.174485,
                        'af_eas_female': 0.174515,
                        'af_afr_male': 0.146568,
                        'af_female': 0.166875,
                        'af_fin_male': 0.216127,
                        'af_oth_female': 0.196364,
                        'af_ami': 0.282366,
                        'af_oth': 0.183892,
                        'af_male': 0.170393,
                        'af_ami_female': 0.273504,
                        'af_afr': 0.148104,
                        'af_eas_male': 0.150179,
                        'af_sas': 0.176684,
                        'af_nfe_female': 0.169528,
                        'af_asj_male': 0.17545,
                        'af_raw': 0.168736,
                        'af_oth_male': 0.170802,
                        'af_nfe_male': 0.168105,
                        'af_asj': 0.174939,
                        'af_amr_male': 0.186368,
                        'af_amr_female': 0.181664,
                        'af_fin': 0.213523,
                        'af_afr_female': 0.149413,
                        'af_sas_male': 0.175731,
                        'af_amr': 0.184334,
                        'af_nfe': 0.168929,
                        'af_eas': 0.161435,
                        'af_ami_male': 0.292056,
                        'af_fin_female': 0.205263,
                        'cadd_rawscore': '0.530047',
                        'cadd_phred': '7.596',
                        'tg_afr': '0.1634',
                        'tg_all': '0.175919',
                        'tg_amr': '0.2104',
                        'tg_eas': '0.1597',
                        'tg_eur': '0.1779',
                        'tg_sas': '0.183'
                    },
                    'source': 'FAVOR',
                    'source_url': 'http://favor.genohub.org/'
                },
                'gene_symbol': [
                    'AGT'
                ],
                'pmid': '20824505',
                'study_parameters': [
                    {
                        'study_parameter_id': '1009568432',
                        'study_type': 'cohort',
                        'study_cases': '68',
                        'study_controls': '357',
                        'p-value': '< 0.05',
                        'biogeographical_groups': 'East Asian'
                    }
                ],
                'phenotype_categories': [
                    'Toxicity'
                ],
                'source': 'pharmGKB',
                'source_url': 'https://www.pharmgkb.org/variantAnnotation/1009360953'
            }
        ]
    }]
}
