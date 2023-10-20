variants = {
    '/variants/freq/{source}': [{
        'params_url': {
            'source': '1000genomes'
        },
        'params': {
            'region': 'chr3:186741137-186742238',
            'funseq_description': 'noncoding',
            'min_alt_freq': '0.1',
            'max_alt_freq': '0.8'
        },
        'response': [
            {
                '_id': '43d4504417fac8ca04517e3d4488208e4457408b7015cd74fdc7be592d686ecf',
                'chr': 'chr3',
                'pos': 186741159,
                'rsid': [
                    'rs5030082'
                ],
                'ref': 'A',
                'alt': 'G',
                'qual': '.',
                'filter': None,
                'annotations': {
                    'freq': {
                        '1000genomes': {
                            'ref:long': 0.5913,
                            'alt:long': 0.4087
                        },
                        'alspac': {
                            'ref:long': 0.6105,
                            'alt:long': 0.3895
                        },
                        'estonian': {
                            'ref:long': 0.6402,
                            'alt:long': 0.3598
                        },
                        'genome_dk': {
                            'ref:long': 0.525,
                            'alt:long': 0.475
                        },
                        'gnomad': {
                            'ref:long': 0.5663,
                            'alt:long': 0.4337
                        },
                        'gonl': {
                            'ref:long': 0.5772,
                            'alt:long': 0.4228
                        },
                        'korean': {
                            'ref:long': 0.7143,
                            'alt:long': 0.2857
                        },
                        'korea1k': {
                            'ref:long': 0.7107,
                            'alt:long': 0.2893
                        },
                        'northernsweden': {
                            'ref:long': 0.5883,
                            'alt:long': 0.4117
                        },
                        'pharmgkb': {
                            'ref:long': 0.5532,
                            'alt:long': 0.4468
                        },
                        'qatari': {
                            'ref:long': 0.6111,
                            'alt:long': 0.3889
                        },
                        'sgdp_prj': {
                            'ref:long': 0.3483,
                            'alt:long': 0.6517
                        },
                        'siberian': {
                            'ref:long': 0.45,
                            'alt:long': 0.55
                        },
                        'tommo': {
                            'ref:long': 0.72,
                            'alt:long': 0.28
                        },
                        'topmed': {
                            'ref:long': 0.5595,
                            'alt:long': 0.4405
                        },
                        'twinsuk': {
                            'ref:long': 0.5871,
                            'alt:long': 0.4129
                        },
                        'dbgap_popfreq': {
                            'ref:long': 0.6007,
                            'alt:long': 0.3993
                        }
                    },
                    'varinfo': '3-186741160-A-G',
                    'vid': '5.33463e+09',
                    'variant_vcf': '3-186741160-A-G',
                    'variant_annovar': '3-186741160-186741160-A-G',
                    'start_position': '1.86741e+08',
                    'end_position': '1.86741e+08',
                    'ref_annovar': 'A',
                    'alt_annovar': 'G',
                    'ref_vcf': 'A',
                    'alt_vcf': 'G',
                    'apc_conservation': 9.54966,
                    'apc_conservation_v2': 9.51849,
                    'apc_epigenetics_active': 0.803684,
                    'apc_epigenetics': 0.692966,
                    'apc_epigenetics_repressed': 0.377742,
                    'apc_epigenetics_transcription': 0.462077,
                    'apc_local_nucleotide_diversity': 1.30443,
                    'apc_local_nucleotide_diversity_v2': 3.01045,
                    'apc_local_nucleotide_diversity_v3': 1.95892,
                    'apc_mappability': 0.556203,
                    'apc_micro_rna': 99.4512,
                    'apc_mutation_density': 3.23779,
                    'apc_protein_function': 20.2494,
                    'apc_protein_function_v2': 4.92793e-10,
                    'apc_protein_function_v3': 2.96949,
                    'apc_proximity_to_coding': 0.79496,
                    'apc_proximity_to_coding_v2': 15.1786,
                    'apc_proximity_to_tsstes': 9.51153,
                    'apc_transcription_factor': 4.69789,
                    'bravo_an': '264690',
                    'bravo_af': '0.44053',
                    'filter_status': 'PASS',
                    'fathmm_xf': '1.64189',
                    'funseq_description': 'noncoding',
                    'af_total': 0.431953,
                    'af_asj_female': 0.505125,
                    'af_eas_female': 0.302503,
                    'af_afr_male': 0.507387,
                    'af_female': 0.433447,
                    'af_fin_male': 0.364387,
                    'af_oth_female': 0.429616,
                    'af_ami': 0.213004,
                    'af_oth': 0.425631,
                    'af_male': 0.430363,
                    'af_ami_female': 0.225322,
                    'af_afr': 0.497704,
                    'af_eas_male': 0.292014,
                    'af_sas': 0.350066,
                    'af_nfe_female': 0.406149,
                    'af_asj_male': 0.512821,
                    'af_raw': 0.431896,
                    'af_oth_male': 0.421456,
                    'af_nfe_male': 0.410411,
                    'af_asj': 0.508745,
                    'af_amr_male': 0.42957,
                    'af_amr_female': 0.450424,
                    'af_fin': 0.367375,
                    'af_afr_female': 0.48946,
                    'af_sas_male': 0.348055,
                    'af_amr': 0.438593,
                    'af_nfe': 0.407944,
                    'af_eas': 0.296855,
                    'af_ami_male': 0.199531,
                    'af_fin_female': 0.376806,
                    'cadd_rawscore': '0.791846',
                    'cadd_phred': '9.849',
                    'tg_afr': '0.5038',
                    'tg_all': '0.408746',
                    'tg_amr': '0.4611',
                    'tg_eas': '0.2946',
                    'tg_eur': '0.4165',
                    'tg_sas': '0.3528'
                },
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/'
            },
            {
                '_id': '3193178755d306ebba4cd839328e5985db87e155e962151783a964578bd77f11',
                'chr': 'chr3',
                'pos': 186741159,
                'rsid': [
                    'rs5030082'
                ],
                'ref': 'A',
                'alt': 'T',
                'qual': '.',
                'filter': None,
                'annotations': {
                    'freq': {
                        '1000genomes': {
                            'ref:long': 0.5913,
                            'alt:long': 0.4087
                        },
                        'alspac': {
                            'ref:long': 0.6105,
                            'alt:long': 0.3895
                        },
                        'estonian': {
                            'ref:long': 0.6402,
                            'alt:long': 0.3598
                        },
                        'genome_dk': {
                            'ref:long': 0.525,
                            'alt:long': 0.475
                        },
                        'gnomad': {
                            'ref:long': 0.5663,
                            'alt:long': 0.4337
                        },
                        'gonl': {
                            'ref:long': 0.5772,
                            'alt:long': 0.4228
                        },
                        'korean': {
                            'ref:long': 0.7143,
                            'alt:long': 0.2857
                        },
                        'korea1k': {
                            'ref:long': 0.7107,
                            'alt:long': 0.2893
                        },
                        'northernsweden': {
                            'ref:long': 0.5883,
                            'alt:long': 0.4117
                        },
                        'pharmgkb': {
                            'ref:long': 0.5532,
                            'alt:long': 0.4468
                        },
                        'qatari': {
                            'ref:long': 0.6111,
                            'alt:long': 0.3889
                        },
                        'sgdp_prj': {
                            'ref:long': 0.3483,
                            'alt:long': 0.6517
                        },
                        'siberian': {
                            'ref:long': 0.45,
                            'alt:long': 0.55
                        },
                        'tommo': {
                            'ref:long': 0.72,
                            'alt:long': 0.28
                        },
                        'topmed': {
                            'ref:long': 0.5595,
                            'alt:long': 0.4405
                        },
                        'twinsuk': {
                            'ref:long': 0.5871,
                            'alt:long': 0.4129
                        },
                        'dbgap_popfreq': {
                            'ref:long': 0.6007,
                            'alt:long': 0.3993
                        }
                    },
                    'varinfo': '3-186741160-A-T',
                    'vid': '5.33463e+09',
                    'variant_vcf': '3-186741160-A-T',
                    'variant_annovar': '3-186741160-186741160-A-T',
                    'start_position': '1.86741e+08',
                    'end_position': '1.86741e+08',
                    'ref_annovar': 'A',
                    'alt_annovar': 'T',
                    'ref_vcf': 'A',
                    'alt_vcf': 'T',
                    'apc_conservation': 9.54966,
                    'apc_conservation_v2': 9.51849,
                    'apc_epigenetics_active': 0.803684,
                    'apc_epigenetics': 0.692966,
                    'apc_epigenetics_repressed': 0.377742,
                    'apc_epigenetics_transcription': 0.462077,
                    'apc_local_nucleotide_diversity': 1.30443,
                    'apc_local_nucleotide_diversity_v2': 3.01045,
                    'apc_local_nucleotide_diversity_v3': 1.95892,
                    'apc_mappability': 0.556203,
                    'apc_micro_rna': 99.4512,
                    'apc_mutation_density': 3.23779,
                    'apc_protein_function': 20.2494,
                    'apc_protein_function_v2': 4.92793e-10,
                    'apc_protein_function_v3': 2.96949,
                    'apc_proximity_to_coding': 0.79496,
                    'apc_proximity_to_coding_v2': 15.1786,
                    'apc_proximity_to_tsstes': 9.51153,
                    'apc_transcription_factor': 4.69789,
                    'fathmm_xf': '1.64189',
                    'funseq_description': 'noncoding',
                    'af_total': 0,
                    'af_asj_female': 0,
                    'af_eas_female': 0,
                    'af_afr_male': 0,
                    'af_female': 0,
                    'af_fin_male': 0,
                    'af_oth_female': 0,
                    'af_ami': 0,
                    'af_oth': 0,
                    'af_male': 0,
                    'af_ami_female': 0,
                    'af_afr': 0,
                    'af_eas_male': 0,
                    'af_sas': 0,
                    'af_nfe_female': 0,
                    'af_asj_male': 0,
                    'af_raw': 0.00000698071,
                    'af_oth_male': 0,
                    'af_nfe_male': 0,
                    'af_asj': 0,
                    'af_amr_male': 0,
                    'af_amr_female': 0,
                    'af_fin': 0,
                    'af_afr_female': 0,
                    'af_sas_male': 0,
                    'af_amr': 0,
                    'af_nfe': 0,
                    'af_eas': 0,
                    'af_ami_male': 0,
                    'af_fin_female': 0,
                    'cadd_rawscore': '0.75421',
                    'cadd_phred': '9.494'
                },
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/'
            },
            {
                '_id': '3e10eb2999945b99958d8f5e1529d182d7dc9ffc8154bd95b394ff692b5f8421',
                'chr': 'chr3',
                'pos': 186741437,
                'rsid': [
                    'rs698078'
                ],
                'ref': 'A',
                'alt': 'G',
                'qual': '.',
                'filter': None,
                'annotations': {
                    'freq': {
                        '1000genomes': {
                            'ref:long': 0.5865,
                            'alt:long': 0.4135
                        },
                        'alspac': {
                            'ref:long': 0.6118,
                            'alt:long': 0.3882
                        },
                        'chileans': {
                            'ref:long': 0.5767,
                            'alt:long': 0.4233
                        },
                        'estonian': {
                            'ref:long': 0.6386,
                            'alt:long': 0.3614
                        },
                        'genome_dk': {
                            'ref:long': 0.525,
                            'alt:long': 0.475
                        },
                        'gnomad': {
                            'ref:long': 0.5603,
                            'alt:long': 0.4397
                        },
                        'gonl': {
                            'ref:long': 0.5762,
                            'alt:long': 0.4238
                        },
                        'hapmap': {
                            'ref:long': 0.5752,
                            'alt:long': 0.4248
                        },
                        'korean': {
                            'ref:long': 0.715,
                            'alt:long': 0.285
                        },
                        'korea1k': {
                            'ref:long': 0.7107,
                            'alt:long': 0.2893
                        },
                        'mgp': {
                            'ref:long': 0.6423,
                            'alt:long': 0.3577
                        },
                        'northernsweden': {
                            'ref:long': 0.5883,
                            'alt:long': 0.4117
                        },
                        'page_study': {
                            'ref:long': 0.5289,
                            'alt:long': 0.4711
                        },
                        'prjeb37584': {
                            'ref:long': 0.7222,
                            'alt:long': 0.2778
                        },
                        'pharmgkb': {
                            'ref:long': 0.5217,
                            'alt:long': 0.4783
                        },
                        'qatari': {
                            'ref:long': 0.6019,
                            'alt:long': 0.3981
                        },
                        'sgdp_prj': {
                            'ref:long': 0.3427,
                            'alt:long': 0.6573
                        },
                        'siberian': {
                            'ref:long': 0.3667,
                            'alt:long': 0.6333
                        },
                        'tommo': {
                            'ref:long': 0.72,
                            'alt:long': 0.28
                        },
                        'topmed': {
                            'ref:long': 0.5528,
                            'alt:long': 0.4472
                        },
                        'twinsuk': {
                            'ref:long': 0.5868,
                            'alt:long': 0.4132
                        },
                        'vietnamese': {
                            'ref:long': 0.6952,
                            'alt:long': 0.3048
                        },
                        'dbgap_popfreq': {
                            'ref:long': 0.5732,
                            'alt:long': 0.4268
                        }
                    },
                    'varinfo': '3-186741438-A-G',
                    'vid': '5.33463e+09',
                    'variant_vcf': '3-186741438-A-G',
                    'variant_annovar': '3-186741438-186741438-A-G',
                    'start_position': '1.86741e+08',
                    'end_position': '1.86741e+08',
                    'ref_annovar': 'A',
                    'alt_annovar': 'G',
                    'ref_vcf': 'A',
                    'alt_vcf': 'G',
                    'apc_conservation': 6.00229,
                    'apc_conservation_v2': 6.71261,
                    'apc_epigenetics_active': 3.53347,
                    'apc_epigenetics': 2.91216,
                    'apc_epigenetics_repressed': 1.66937,
                    'apc_epigenetics_transcription': 1.85445,
                    'apc_local_nucleotide_diversity': 1.30443,
                    'apc_local_nucleotide_diversity_v2': 2.66148,
                    'apc_local_nucleotide_diversity_v3': 1.85315,
                    'apc_mappability': 9.95131,
                    'apc_micro_rna': 99.4512,
                    'apc_mutation_density': 2.85307,
                    'apc_protein_function': 20.2494,
                    'apc_protein_function_v2': 4.92793e-10,
                    'apc_protein_function_v3': 2.96949,
                    'apc_proximity_to_coding': 3.28346,
                    'apc_proximity_to_coding_v2': 15.1786,
                    'apc_proximity_to_tsstes': 9.88041,
                    'apc_transcription_factor': 3.14279,
                    'bravo_an': '264690',
                    'bravo_af': '0.447221',
                    'filter_status': 'PASS',
                    'fathmm_xf': '0.616397',
                    'funseq_description': 'noncoding',
                    'af_total': 0.437774,
                    'af_asj_female': 0.506818,
                    'af_eas_female': 0.301796,
                    'af_afr_male': 0.524365,
                    'af_female': 0.439569,
                    'af_fin_male': 0.364165,
                    'af_oth_female': 0.435337,
                    'af_ami': 0.211111,
                    'af_oth': 0.432558,
                    'af_male': 0.435864,
                    'af_ami_female': 0.223404,
                    'af_afr': 0.515211,
                    'af_eas_male': 0.290974,
                    'af_sas': 0.350099,
                    'af_nfe_female': 0.406635,
                    'af_asj_male': 0.512179,
                    'af_raw': 0.437923,
                    'af_oth_male': 0.429658,
                    'af_nfe_male': 0.410892,
                    'af_asj': 0.509337,
                    'af_amr_male': 0.434608,
                    'af_amr_female': 0.454391,
                    'af_fin': 0.366839,
                    'af_afr_female': 0.507417,
                    'af_sas_male': 0.347984,
                    'af_amr': 0.443165,
                    'af_nfe': 0.408426,
                    'af_eas': 0.295977,
                    'af_ami_male': 0.197674,
                    'af_fin_female': 0.3753,
                    'cadd_rawscore': '0.17923',
                    'cadd_phred': '3.792',
                    'tg_afr': '0.5197',
                    'tg_all': '0.413538',
                    'tg_amr': '0.464',
                    'tg_eas': '0.2946',
                    'tg_eur': '0.4175',
                    'tg_sas': '0.3528'
                },
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/'
            }]}
    ],
    '/variants/{id}': [{
        'params_url': {
            'id': '77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb'
        },
        'response': {
            '_id': '77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb',
            'chr': 'chr3',
            'pos': 186742137,
            'rsid': [
                'rs710446'
            ],
            'ref': 'T',
            'alt': 'C',
            'qual': '.',
            'filter': None,
            'annotations': {
                'freq': {
                    '1000genomes': {
                        'ref:long': 0.5847,
                        'alt:long': 0.4153
                    },
                    'alspac': {
                        'ref:long': 0.6079,
                        'alt:long': 0.3921
                    },
                    'estonian': {
                        'ref:long': 0.6328,
                        'alt:long': 0.3672
                    },
                    'exac': {
                        'ref:long': 0.5846,
                        'alt:long': 0.4154
                    },
                    'finrisk': {
                        'ref:long': 0.5691,
                        'alt:long': 0.4309
                    },
                    'genome_dk': {
                        'ref:long': 0.525,
                        'alt:long': 0.475
                    },
                    'gnomad': {
                        'ref:long': 0.5575,
                        'alt:long': 0.4425
                    },
                    'gnomad_exomes': {
                        'ref:long': 0.5838,
                        'alt:long': 0.4162
                    },
                    'goesp': {
                        'ref:long': 0.5581,
                        'alt:long': 0.4419
                    },
                    'gonl': {
                        'ref:long': 0.5731,
                        'alt:long': 0.4269
                    },
                    'hgdp_stanford': {
                        'ref:long': 0.5749,
                        'alt:long': 0.4251
                    },
                    'hapmap': {
                        'ref:long': 0.5771,
                        'alt:long': 0.4229
                    },
                    'korean': {
                        'ref:long': 0.7154,
                        'alt:long': 0.2846
                    },
                    'korea1k': {
                        'ref:long': 0.7096,
                        'alt:long': 0.2904
                    },
                    'mgp': {
                        'ref:long': 0.5562,
                        'alt:long': 0.4438
                    },
                    'northernsweden': {
                        'ref:long': 0.5867,
                        'alt:long': 0.4133
                    },
                    'page_study': {
                        'ref:long': 0.526,
                        'alt:long': 0.474
                    },
                    'prjeb36033': {
                        'ref:long': 0.425,
                        'alt:long': 0.575
                    },
                    'pharmgkb': {
                        'ref:long': 0.5435,
                        'alt:long': 0.4565
                    },
                    'qatari': {
                        'ref:long': 0.5972,
                        'alt:long': 0.4028
                    },
                    'sgdp_prj': {
                        'ref:long': 0.3427,
                        'alt:long': 0.6573
                    },
                    'siberian': {
                        'ref:long': 0.3667,
                        'alt:long': 0.6333
                    },
                    'tommo': {
                        'ref:long': 0.7084,
                        'alt:long': 0.2916
                    },
                    'topmed': {
                        'ref:long': 0.5495,
                        'alt:long': 0.4505
                    },
                    'twinsuk': {
                        'ref:long': 0.5844,
                        'alt:long': 0.4156
                    },
                    'vietnamese': {
                        'ref:long': 0.6775,
                        'alt:long': 0.3225
                    },
                    'dbgap_popfreq': {
                        'ref:long': 0.5805,
                        'alt:long': 0.4195
                    }
                },
                'varinfo': '3-186742138-T-C',
                'vid': '5.33464e+09',
                'variant_vcf': '3-186742138-T-C',
                'variant_annovar': '3-186742138-186742138-T-C',
                'start_position': '1.86742e+08',
                'end_position': '1.86742e+08',
                'ref_annovar': 'T',
                'alt_annovar': 'C',
                'ref_vcf': 'T',
                'alt_vcf': 'C',
                'apc_conservation': 16.2472,
                'apc_conservation_v2': 15.5978,
                'apc_epigenetics_active': 6.32647,
                'apc_epigenetics': 6.80677,
                'apc_epigenetics_repressed': 9.86256,
                'apc_epigenetics_transcription': 3.65527,
                'apc_local_nucleotide_diversity': 1.30443,
                'apc_local_nucleotide_diversity_v2': 3.36836,
                'apc_local_nucleotide_diversity_v3': 2.34209,
                'apc_mappability': 8.95186,
                'apc_micro_rna': 99.4512,
                'apc_mutation_density': 3.61778,
                'apc_protein_function': 20.9113,
                'apc_protein_function_v2': 20.9113,
                'apc_protein_function_v3': 20.9113,
                'apc_proximity_to_coding': 26.192,
                'apc_proximity_to_coding_v2': 26.4579,
                'apc_proximity_to_tsstes': 11.0606,
                'apc_transcription_factor': 4.69789,
                'bravo_an': '264690',
                'bravo_af': '0.45047',
                'filter_status': 'PASS',
                'polyphen2_hdiv_score': '0',
                'polyphen2_hvar_score': '0',
                'mutation_taster_score': '1',
                'mutation_assessor_score': '-2.24',
                'metasvm_pred': None,
                'fathmm_xf': '16.1036',
                'funseq_value': '3',
                'funseq_description': 'coding'
            },
            'source': 'FAVOR',
            'source_url': 'http://favor.genohub.org/'
        }
    }],
    '/variants': [{
        'params': {
            'region': 'chr3:186741137-186742238',
            'rsid': 'rs5030082',
            'funseq_description': 'noncoding'
        },
        'response': [
            {
                '_id': '43d4504417fac8ca04517e3d4488208e4457408b7015cd74fdc7be592d686ecf',
                'chr': 'chr3',
                'pos': 186741159,
                'rsid': [
                    'rs5030082'
                ],
                'ref': 'A',
                'alt': 'G',
                'qual': '.',
                'filter': None,
                'annotations': {
                    'freq': {
                        '1000genomes': {
                            'ref:long': 0.5913,
                            'alt:long': 0.4087
                        },
                        'alspac': {
                            'ref:long': 0.6105,
                            'alt:long': 0.3895
                        },
                        'estonian': {
                            'ref:long': 0.6402,
                            'alt:long': 0.3598
                        },
                        'genome_dk': {
                            'ref:long': 0.525,
                            'alt:long': 0.475
                        },
                        'gnomad': {
                            'ref:long': 0.5663,
                            'alt:long': 0.4337
                        },
                        'gonl': {
                            'ref:long': 0.5772,
                            'alt:long': 0.4228
                        },
                        'korean': {
                            'ref:long': 0.7143,
                            'alt:long': 0.2857
                        },
                        'korea1k': {
                            'ref:long': 0.7107,
                            'alt:long': 0.2893
                        },
                        'northernsweden': {
                            'ref:long': 0.5883,
                            'alt:long': 0.4117
                        },
                        'pharmgkb': {
                            'ref:long': 0.5532,
                            'alt:long': 0.4468
                        },
                        'qatari': {
                            'ref:long': 0.6111,
                            'alt:long': 0.3889
                        },
                        'sgdp_prj': {
                            'ref:long': 0.3483,
                            'alt:long': 0.6517
                        },
                        'siberian': {
                            'ref:long': 0.45,
                            'alt:long': 0.55
                        },
                        'tommo': {
                            'ref:long': 0.72,
                            'alt:long': 0.28
                        },
                        'topmed': {
                            'ref:long': 0.5595,
                            'alt:long': 0.4405
                        },
                        'twinsuk': {
                            'ref:long': 0.5871,
                            'alt:long': 0.4129
                        },
                        'dbgap_popfreq': {
                            'ref:long': 0.6007,
                            'alt:long': 0.3993
                        }
                    },
                    'varinfo': '3-186741160-A-G',
                    'vid': '5.33463e+09',
                    'variant_vcf': '3-186741160-A-G',
                    'variant_annovar': '3-186741160-186741160-A-G',
                    'start_position': '1.86741e+08',
                    'end_position': '1.86741e+08',
                    'ref_annovar': 'A',
                    'alt_annovar': 'G',
                    'ref_vcf': 'A',
                    'alt_vcf': 'G',
                    'apc_conservation': 9.54966,
                    'apc_conservation_v2': 9.51849,
                    'apc_epigenetics_active': 0.803684,
                    'apc_epigenetics': 0.692966,
                    'apc_epigenetics_repressed': 0.377742,
                    'apc_epigenetics_transcription': 0.462077,
                    'apc_local_nucleotide_diversity': 1.30443,
                    'apc_local_nucleotide_diversity_v2': 3.01045,
                    'apc_local_nucleotide_diversity_v3': 1.95892,
                    'apc_mappability': 0.556203,
                    'apc_micro_rna': 99.4512,
                    'apc_mutation_density': 3.23779,
                    'apc_protein_function': 20.2494,
                    'apc_protein_function_v2': 4.92793e-10,
                    'apc_protein_function_v3': 2.96949,
                    'apc_proximity_to_coding': 0.79496,
                    'apc_proximity_to_coding_v2': 15.1786,
                    'apc_proximity_to_tsstes': 9.51153,
                    'apc_transcription_factor': 4.69789,
                    'bravo_an': '264690',
                    'bravo_af': '0.44053',
                    'filter_status': 'PASS',
                    'fathmm_xf': '1.64189',
                    'funseq_description': 'noncoding',
                    'af_total': 0.431953,
                    'af_asj_female': 0.505125,
                    'af_eas_female': 0.302503,
                    'af_afr_male': 0.507387,
                    'af_female': 0.433447,
                    'af_fin_male': 0.364387,
                    'af_oth_female': 0.429616,
                    'af_ami': 0.213004,
                    'af_oth': 0.425631,
                    'af_male': 0.430363,
                    'af_ami_female': 0.225322,
                    'af_afr': 0.497704,
                    'af_eas_male': 0.292014,
                    'af_sas': 0.350066,
                    'af_nfe_female': 0.406149,
                    'af_asj_male': 0.512821,
                    'af_raw': 0.431896,
                    'af_oth_male': 0.421456,
                    'af_nfe_male': 0.410411,
                    'af_asj': 0.508745,
                    'af_amr_male': 0.42957,
                    'af_amr_female': 0.450424,
                    'af_fin': 0.367375,
                    'af_afr_female': 0.48946,
                    'af_sas_male': 0.348055,
                    'af_amr': 0.438593,
                    'af_nfe': 0.407944,
                    'af_eas': 0.296855,
                    'af_ami_male': 0.199531,
                    'af_fin_female': 0.376806,
                    'cadd_rawscore': '0.791846',
                    'cadd_phred': '9.849',
                    'tg_afr': '0.5038',
                    'tg_all': '0.408746',
                    'tg_amr': '0.4611',
                    'tg_eas': '0.2946',
                    'tg_eur': '0.4165',
                    'tg_sas': '0.3528'
                },
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/'
            },
            {
                '_id': '3193178755d306ebba4cd839328e5985db87e155e962151783a964578bd77f11',
                'chr': 'chr3',
                'pos': 186741159,
                'rsid': [
                    'rs5030082'
                ],
                'ref': 'A',
                'alt': 'T',
                'qual': '.',
                'filter': None,
                'annotations': {
                    'freq': {
                        '1000genomes': {
                            'ref:long': 0.5913,
                            'alt:long': 0.4087
                        },
                        'alspac': {
                            'ref:long': 0.6105,
                            'alt:long': 0.3895
                        },
                        'estonian': {
                            'ref:long': 0.6402,
                            'alt:long': 0.3598
                        },
                        'genome_dk': {
                            'ref:long': 0.525,
                            'alt:long': 0.475
                        },
                        'gnomad': {
                            'ref:long': 0.5663,
                            'alt:long': 0.4337
                        },
                        'gonl': {
                            'ref:long': 0.5772,
                            'alt:long': 0.4228
                        },
                        'korean': {
                            'ref:long': 0.7143,
                            'alt:long': 0.2857
                        },
                        'korea1k': {
                            'ref:long': 0.7107,
                            'alt:long': 0.2893
                        },
                        'northernsweden': {
                            'ref:long': 0.5883,
                            'alt:long': 0.4117
                        },
                        'pharmgkb': {
                            'ref:long': 0.5532,
                            'alt:long': 0.4468
                        },
                        'qatari': {
                            'ref:long': 0.6111,
                            'alt:long': 0.3889
                        },
                        'sgdp_prj': {
                            'ref:long': 0.3483,
                            'alt:long': 0.6517
                        },
                        'siberian': {
                            'ref:long': 0.45,
                            'alt:long': 0.55
                        },
                        'tommo': {
                            'ref:long': 0.72,
                            'alt:long': 0.28
                        },
                        'topmed': {
                            'ref:long': 0.5595,
                            'alt:long': 0.4405
                        },
                        'twinsuk': {
                            'ref:long': 0.5871,
                            'alt:long': 0.4129
                        },
                        'dbgap_popfreq': {
                            'ref:long': 0.6007,
                            'alt:long': 0.3993
                        }
                    },
                    'varinfo': '3-186741160-A-T',
                    'vid': '5.33463e+09',
                    'variant_vcf': '3-186741160-A-T',
                    'variant_annovar': '3-186741160-186741160-A-T',
                    'start_position': '1.86741e+08',
                    'end_position': '1.86741e+08',
                    'ref_annovar': 'A',
                    'alt_annovar': 'T',
                    'ref_vcf': 'A',
                    'alt_vcf': 'T',
                    'apc_conservation': 9.54966,
                    'apc_conservation_v2': 9.51849,
                    'apc_epigenetics_active': 0.803684,
                    'apc_epigenetics': 0.692966,
                    'apc_epigenetics_repressed': 0.377742,
                    'apc_epigenetics_transcription': 0.462077,
                    'apc_local_nucleotide_diversity': 1.30443,
                    'apc_local_nucleotide_diversity_v2': 3.01045,
                    'apc_local_nucleotide_diversity_v3': 1.95892,
                    'apc_mappability': 0.556203,
                    'apc_micro_rna': 99.4512,
                    'apc_mutation_density': 3.23779,
                    'apc_protein_function': 20.2494,
                    'apc_protein_function_v2': 4.92793e-10,
                    'apc_protein_function_v3': 2.96949,
                    'apc_proximity_to_coding': 0.79496,
                    'apc_proximity_to_coding_v2': 15.1786,
                    'apc_proximity_to_tsstes': 9.51153,
                    'apc_transcription_factor': 4.69789,
                    'fathmm_xf': '1.64189',
                    'funseq_description': 'noncoding',
                    'af_total': 0,
                    'af_asj_female': 0,
                    'af_eas_female': 0,
                    'af_afr_male': 0,
                    'af_female': 0,
                    'af_fin_male': 0,
                    'af_oth_female': 0,
                    'af_ami': 0,
                    'af_oth': 0,
                    'af_male': 0,
                    'af_ami_female': 0,
                    'af_afr': 0,
                    'af_eas_male': 0,
                    'af_sas': 0,
                    'af_nfe_female': 0,
                    'af_asj_male': 0,
                    'af_raw': 0.00000698071,
                    'af_oth_male': 0,
                    'af_nfe_male': 0,
                    'af_asj': 0,
                    'af_amr_male': 0,
                    'af_amr_female': 0,
                    'af_fin': 0,
                    'af_afr_female': 0,
                    'af_sas_male': 0,
                    'af_amr': 0,
                    'af_nfe': 0,
                    'af_eas': 0,
                    'af_ami_male': 0,
                    'af_fin_female': 0,
                    'cadd_rawscore': '0.75421',
                    'cadd_phred': '9.494'
                },
                'source': 'FAVOR',
                'source_url': 'http://favor.genohub.org/'
            }
        ]
    }]
}
