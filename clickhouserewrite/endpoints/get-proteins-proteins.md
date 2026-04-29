# `GET /proteins/proteins`

**Status:** ❌ AQL-only

**Router file:** [`src/routers/datatypeRouters/edges/proteins_proteins.ts`](../../src/routers/datatypeRouters/edges/proteins_proteins.ts)

## Description

Retrieve protein-protein interactions.<br>   Set verbose = true to retrieve full info on the proteins. <br>   Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br>   protein_name = CTCF, <br>   uniprot_name = CTCF_HUMAN, <br>   uniprot_full_name = Transcriptional repressor CTCF, <br>   dbxrefs = P49711, <br>   detection_method = affinity chromatography technology, <br>   interaction_type = physical association, <br>   pmid = 28514442, <br>   label = affinity chromatography technology, <br>   method = physical association, <br>   source = BioGRID. <br>   The limit parameter controls the page size and can not exceed 250. <br>   Pagination is 0-based.

## OpenAPI excerpt

```json
{
  "operationId": "proteinsProteins",
  "description": "Retrieve protein-protein interactions.<br>   Set verbose = true to retrieve full info on the proteins. <br>   Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br>   protein_name = CTCF, <br>   uniprot_name = CTCF_HUMAN, <br>   uniprot_full_name = Transcriptional repressor CTCF, <br>   dbxrefs = P49711, <br>   detection_method = affinity chromatography technology, <br>   interaction_type = physical association, <br>   pmid = 28514442, <br>   label = affinity chromatography technology, <br>   method = physical association, <br>   source = BioGRID. <br>   The limit parameter controls the page size and can not exceed 250. <br>   Pagination is 0-based.",
  "parameters": [
    {
      "name": "protein_id",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "protein_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "uniprot_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "uniprot_full_name",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "dbxrefs",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "pmid",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "name": "detection_method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "3D electron microscopy",
          "Split renilla luciferase complementation",
          "acetylase assay",
          "adp ribosylase assay",
          "affinity chromatography technology",
          "affinity technology",
          "aggregation assay",
          "amplified luminescent proximity homogeneous assay",
          "ampylation assay",
          "anti bait coimmunoprecipitation",
          "anti tag coimmunoprecipitation",
          "antibody array",
          "array technology",
          "atomic force microscopy",
          "atpase assay",
          "avexis",
          "barcode fusion genetics two hybrid",
          "bead aggregation assay",
          "beta galactosidase complementation",
          "beta lactamase complementation",
          "bimolecular fluorescence complementation",
          "bio-layer interferometry",
          "biochemical",
          "bioluminescence resonance energy transfer",
          "biophysical",
          "biosensor",
          "blue native page",
          "chromatin immunoprecipitation array",
          "chromatin immunoprecipitation assay",
          "chromatography technology",
          "circular dichroism",
          "classical fluorescence spectroscopy",
          "cleavage assay",
          "coimmunoprecipitation",
          "comigration in gel electrophoresis",
          "comigration in non denaturing gel electrophoresis",
          "comigration in sds page",
          "competition binding",
          "confocal microscopy",
          "cosedimentation",
          "cosedimentation in solution",
          "cosedimentation through density gradient",
          "cross-linking study",
          "de-ADP-ribosylation assay",
          "deacetylase assay",
          "decarboxylation assay",
          "demethylase assay",
          "detection by mass spectrometry",
          "deubiquitinase assay",
          "differential scanning calorimetry",
          "dihydrofolate reductase reconstruction",
          "display technology",
          "dynamic light scattering",
          "electron diffraction",
          "electron microscopy",
          "electron microscopy 3D helical reconstruction",
          "electron microscopy 3D single particle reconstruction",
          "electron paramagnetic resonance",
          "electron tomography",
          "electrophoretic mobility shift assay",
          "electrophoretic mobility supershift assay",
          "electrophoretic mobility-based method",
          "enzymatic footprinting",
          "enzymatic study",
          "enzyme linked immunosorbent assay",
          "experimental interaction detection",
          "far western blotting",
          "field flow fractionation",
          "filamentous phage display",
          "filter binding",
          "filter trap assay",
          "fluorescence correlation spectroscopy",
          "fluorescence microscopy",
          "fluorescence polarization spectroscopy",
          "fluorescence recovery after photobleaching",
          "fluorescence technology",
          "fluorescence-activated cell sorting",
          "fluorescent resonance energy transfer",
          "footprinting",
          "force spectroscopy",
          "gal4 vp16 complementation",
          "gdp/gtp exchange assay",
          "glycosylase assay",
          "gtpase assay",
          "homogeneous time resolved fluorescence",
          "hydroxylase assay",
          "imaging technique",
          "immunodepleted coimmunoprecipitation",
          "in-gel kinase assay",
          "inference by socio-affinity scoring",
          "infrared spectroscopy",
          "interaction detection method",
          "interactome parallel affinity capture",
          "ion exchange chromatography",
          "ion mobility mass spectrometry of complexes",
          "isothermal titration calorimetry",
          "kinase homogeneous time resolved fluorescence",
          "kinase scintillation proximity assay",
          "lambda phage display",
          "lambda repressor two hybrid",
          "lex-a dimerization assay",
          "lexa b52 complementation",
          "lexa vp16 complementation",
          "light microscopy",
          "light scattering",
          "lipoprotein cleavage assay",
          "luminescence based mammalian interactome mapping",
          "mammalian protein protein interaction trap",
          "mass spectrometry studies of complexes",
          "mass spectrometry study of hydrogen/deuterium exchange",
          "methyltransferase assay",
          "methyltransferase radiometric assay",
          "microscale thermophoresis",
          "molecular sieving",
          "mrna display",
          "myristoylase assay",
          "neddylase assay",
          "nuclear magnetic resonance",
          "nuclease assay",
          "oxidase assay",
          "oxidoreductase assay",
          "p8 filamentous phage display",
          "palmitoylase assay",
          "peptide array",
          "phage display",
          "phosphatase assay",
          "phosphotransferase assay",
          "polymerization",
          "probe interaction assay",
          "protease accessibility laddering",
          "protease assay",
          "protein array",
          "protein complementation assay",
          "protein cross-linking with a bifunctional reagent",
          "protein kinase assay",
          "protein phosphatase assay",
          "protein three hybrid",
          "proteinchip(r) on a surface-enhanced laser desorption/ionization",
          "proximity labelling technology",
          "proximity ligation assay",
          "proximity-dependent biotin identification",
          "pull down",
          "reverse phase chromatography",
          "reverse ras recruitment system",
          "reverse two hybrid",
          "ribonuclease assay",
          "rna immunoprecipitation",
          "rna interference",
          "sandwich immunoassay",
          "saturation binding",
          "scanning electron microscopy",
          "scintillation proximity assay",
          "small angle neutron scattering",
          "solid phase assay",
          "solid state nmr",
          "solution state nmr",
          "split firefly luciferase complementation",
          "split luciferase complementation",
          "static light scattering",
          "sumoylase assay",
          "super-resolution microscopy",
          "surface plasmon resonance",
          "surface plasmon resonance array",
          "t7 phage display",
          "tandem affinity purification",
          "thermal shift binding",
          "three hybrid",
          "tox-r dimerization assay",
          "transcriptional complementation assay",
          "transmission electron microscopy",
          "two hybrid",
          "two hybrid array",
          "two hybrid bait and prey pooling approach",
          "two hybrid fragment pooling approach",
          "two hybrid pooling approach",
          "two hybrid prey pooling approach",
          "ubiquitin reconstruction",
          "ubiquitinase assay",
          "ultraviolet-visible spectroscopy",
          "unspecified method",
          "validated two hybrid",
          "virotrap",
          "x ray scattering",
          "x-ray crystallography",
          "x-ray fiber diffraction",
          "yeast display",
          "zymography"
        ]
      }
    },
    {
      "name": "interaction_type",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "acetylation reaction",
          "adp ribosylation reaction",
          "ampylation reaction",
          "association",
          "atpase reaction",
          "cleavage reaction",
          "colocalization",
          "covalent binding",
          "de-ADP-ribosylation reaction",
          "deacetylation reaction",
          "demethylation reaction",
          "deneddylation reaction",
          "dephosphorylation reaction",
          "deubiquitination reaction",
          "direct interaction",
          "disulfide bond",
          "dna cleavage",
          "enzymatic reaction",
          "glycosylation reaction",
          "gtpase reaction",
          "guanine nucleotide exchange factor reaction",
          "hydroxylation reaction",
          "lipid addition",
          "lipoprotein cleavage reaction",
          "methylation reaction",
          "myristoylation reaction",
          "neddylation reaction",
          "oxidoreductase activity electron transfer reaction",
          "palmitoylation reaction",
          "phosphorylation reaction",
          "phosphotransfer reaction",
          "physical association",
          "proline isomerization  reaction",
          "protein cleavage",
          "proximity",
          "putative self interaction",
          "rna cleavage",
          "self interaction",
          "sumoylation reaction",
          "transglutamination reaction",
          "ubiquitination reaction"
        ]
      }
    },
    {
      "name": "label",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "3D electron microscopy",
          "Split renilla luciferase complementation",
          "acetylase assay",
          "adp ribosylase assay",
          "affinity chromatography technology",
          "affinity technology",
          "aggregation assay",
          "amplified luminescent proximity homogeneous assay",
          "ampylation assay",
          "anti bait coimmunoprecipitation",
          "anti tag coimmunoprecipitation",
          "antibody array",
          "array technology",
          "atomic force microscopy",
          "atpase assay",
          "avexis",
          "barcode fusion genetics two hybrid",
          "bead aggregation assay",
          "beta galactosidase complementation",
          "beta lactamase complementation",
          "bimolecular fluorescence complementation",
          "bio-layer interferometry",
          "biochemical",
          "bioluminescence resonance energy transfer",
          "biophysical",
          "biosensor",
          "blue native page",
          "chromatin immunoprecipitation array",
          "chromatin immunoprecipitation assay",
          "chromatography technology",
          "circular dichroism",
          "classical fluorescence spectroscopy",
          "cleavage assay",
          "coimmunoprecipitation",
          "comigration in gel electrophoresis",
          "comigration in non denaturing gel electrophoresis",
          "comigration in sds page",
          "competition binding",
          "confocal microscopy",
          "cosedimentation",
          "cosedimentation in solution",
          "cosedimentation through density gradient",
          "cross-linking study",
          "de-ADP-ribosylation assay",
          "deacetylase assay",
          "decarboxylation assay",
          "demethylase assay",
          "detection by mass spectrometry",
          "deubiquitinase assay",
          "differential scanning calorimetry",
          "dihydrofolate reductase reconstruction",
          "display technology",
          "dynamic light scattering",
          "electron diffraction",
          "electron microscopy",
          "electron microscopy 3D helical reconstruction",
          "electron microscopy 3D single particle reconstruction",
          "electron paramagnetic resonance",
          "electron tomography",
          "electrophoretic mobility shift assay",
          "electrophoretic mobility supershift assay",
          "electrophoretic mobility-based method",
          "enzymatic footprinting",
          "enzymatic study",
          "enzyme linked immunosorbent assay",
          "experimental interaction detection",
          "far western blotting",
          "field flow fractionation",
          "filamentous phage display",
          "filter binding",
          "filter trap assay",
          "fluorescence correlation spectroscopy",
          "fluorescence microscopy",
          "fluorescence polarization spectroscopy",
          "fluorescence recovery after photobleaching",
          "fluorescence technology",
          "fluorescence-activated cell sorting",
          "fluorescent resonance energy transfer",
          "footprinting",
          "force spectroscopy",
          "gal4 vp16 complementation",
          "gdp/gtp exchange assay",
          "glycosylase assay",
          "gtpase assay",
          "homogeneous time resolved fluorescence",
          "hydroxylase assay",
          "imaging technique",
          "immunodepleted coimmunoprecipitation",
          "in-gel kinase assay",
          "inference by socio-affinity scoring",
          "infrared spectroscopy",
          "interaction detection method",
          "interactome parallel affinity capture",
          "ion exchange chromatography",
          "ion mobility mass spectrometry of complexes",
          "isothermal titration calorimetry",
          "kinase homogeneous time resolved fluorescence",
          "kinase scintillation proximity assay",
          "lambda phage display",
          "lambda repressor two hybrid",
          "lex-a dimerization assay",
          "lexa b52 complementation",
          "lexa vp16 complementation",
          "light microscopy",
          "light scattering",
          "lipoprotein cleavage assay",
          "luminescence based mammalian interactome mapping",
          "mammalian protein protein interaction trap",
          "mass spectrometry studies of complexes",
          "mass spectrometry study of hydrogen/deuterium exchange",
          "methyltransferase assay",
          "methyltransferase radiometric assay",
          "microscale thermophoresis",
          "molecular sieving",
          "mrna display",
          "myristoylase assay",
          "neddylase assay",
          "nuclear magnetic resonance",
          "nuclease assay",
          "oxidase assay",
          "oxidoreductase assay",
          "p8 filamentous phage display",
          "palmitoylase assay",
          "peptide array",
          "phage display",
          "phosphatase assay",
          "phosphotransferase assay",
          "polymerization",
          "probe interaction assay",
          "protease accessibility laddering",
          "protease assay",
          "protein array",
          "protein complementation assay",
          "protein cross-linking with a bifunctional reagent",
          "protein kinase assay",
          "protein phosphatase assay",
          "protein three hybrid",
          "proteinchip(r) on a surface-enhanced laser desorption/ionization",
          "proximity labelling technology",
          "proximity ligation assay",
          "proximity-dependent biotin identification",
          "pull down",
          "reverse phase chromatography",
          "reverse ras recruitment system",
          "reverse two hybrid",
          "ribonuclease assay",
          "rna immunoprecipitation",
          "rna interference",
          "sandwich immunoassay",
          "saturation binding",
          "scanning electron microscopy",
          "scintillation proximity assay",
          "small angle neutron scattering",
          "solid phase assay",
          "solid state nmr",
          "solution state nmr",
          "split firefly luciferase complementation",
          "split luciferase complementation",
          "static light scattering",
          "sumoylase assay",
          "super-resolution microscopy",
          "surface plasmon resonance",
          "surface plasmon resonance array",
          "t7 phage display",
          "tandem affinity purification",
          "thermal shift binding",
          "three hybrid",
          "tox-r dimerization assay",
          "transcriptional complementation assay",
          "transmission electron microscopy",
          "two hybrid",
          "two hybrid array",
          "two hybrid bait and prey pooling approach",
          "two hybrid fragment pooling approach",
          "two hybrid pooling approach",
          "two hybrid prey pooling approach",
          "ubiquitin reconstruction",
          "ubiquitinase assay",
          "ultraviolet-visible spectroscopy",
          "unspecified method",
          "validated two hybrid",
          "virotrap",
          "x ray scattering",
          "x-ray crystallography",
          "x-ray fiber diffraction",
          "yeast display",
          "zymography"
        ]
      }
    },
    {
      "name": "method",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "acetylation reaction",
          "acetylation reaction, direct interaction",
          "adp ribosylation reaction",
          "adp ribosylation reaction, direct interaction",
          "adp ribosylation reaction, direct interaction, enzymatic reaction",
          "ampylation reaction",
          "association",
          "association, colocalization",
          "association, direct interaction",
          "association, phosphorylation reaction",
          "association, physical association",
          "atpase reaction",
          "cleavage reaction",
          "cleavage reaction, direct interaction",
          "cleavage reaction, enzymatic reaction",
          "cleavage reaction, protein cleavage",
          "colocalization",
          "colocalization, association",
          "colocalization, association, physical association",
          "colocalization, direct interaction",
          "colocalization, direct interaction, physical association",
          "colocalization, direct interaction, physical association, association",
          "colocalization, physical association",
          "covalent binding",
          "covalent binding, association",
          "covalent binding, direct interaction",
          "de-ADP-ribosylation reaction",
          "deacetylation reaction",
          "deacetylation reaction, direct interaction",
          "demethylation reaction",
          "deneddylation reaction",
          "dephosphorylation reaction",
          "dephosphorylation reaction, direct interaction",
          "dephosphorylation reaction, physical association",
          "deubiquitination reaction",
          "direct interaction",
          "direct interaction, association",
          "direct interaction, association, physical association",
          "direct interaction, deacetylation reaction",
          "direct interaction, enzymatic reaction",
          "direct interaction, glycosylation reaction",
          "direct interaction, methylation reaction",
          "direct interaction, phosphorylation reaction",
          "direct interaction, physical association",
          "direct interaction, physical association, association",
          "disulfide bond",
          "disulfide bond, association",
          "disulfide bond, direct interaction",
          "disulfide bond, physical association",
          "dna cleavage",
          "enzymatic reaction",
          "glycosylation reaction",
          "gtpase reaction",
          "guanine nucleotide exchange factor reaction",
          "hydroxylation reaction",
          "hydroxylation reaction, association",
          "lipoprotein cleavage reaction",
          "methylation reaction",
          "myristoylation reaction, lipid addition",
          "neddylation reaction",
          "neddylation reaction, direct interaction",
          "oxidoreductase activity electron transfer reaction",
          "palmitoylation reaction",
          "phosphorylation reaction",
          "phosphotransfer reaction",
          "physical association",
          "physical association, association",
          "physical association, association, direct interaction",
          "physical association, colocalization",
          "physical association, direct interaction",
          "physical association, phosphorylation reaction",
          "proline isomerization  reaction, direct interaction",
          "protein cleavage",
          "protein cleavage, direct interaction",
          "protein cleavage, direct interaction, association",
          "protein cleavage, phosphorylation reaction",
          "proximity",
          "proximity, direct interaction",
          "proximity, physical association",
          "putative self interaction",
          "rna cleavage",
          "self interaction",
          "self interaction, physical association",
          "sumoylation reaction",
          "sumoylation reaction, direct interaction",
          "transglutamination reaction",
          "ubiquitination reaction",
          "ubiquitination reaction, association",
          "ubiquitination reaction, direct interaction"
        ]
      }
    },
    {
      "name": "source",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "BioGRID",
          "BioGRID; IntAct",
          "IntAct",
          "IntAct; BioGRID"
        ]
      }
    },
    {
      "name": "organism",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "Mus musculus",
          "Homo sapiens"
        ],
        "default": "Homo sapiens"
      }
    },
    {
      "name": "verbose",
      "in": "query",
      "required": false,
      "schema": {
        "type": "string",
        "enum": [
          "true",
          "false"
        ],
        "default": "false"
      }
    },
    {
      "name": "page",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number",
        "default": 0
      }
    },
    {
      "name": "limit",
      "in": "query",
      "required": false,
      "schema": {
        "type": "number"
      }
    }
  ],
  "responses": {
    "200": {
      "description": "Successful response",
      "content": {
        "application/json": {
          "schema": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "protein 1": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "_id": {
                            "type": "string"
                          },
                          "name": {
                            "type": "string",
                            "nullable": true
                          },
                          "uniprot_names": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "uniprot_full_names": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "uniprot_ids": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "MANE_Select": {
                            "type": "boolean",
                            "nullable": true
                          },
                          "organism": {
                            "type": "string"
                          },
                          "source": {
                            "type": "string"
                          },
                          "source_url": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "_id",
                          "organism",
                          "source",
                          "source_url"
                        ],
                        "additionalProperties": false
                      }
                    }
                  ]
                },
                "protein 2": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "_id": {
                            "type": "string"
                          },
                          "name": {
                            "type": "string",
                            "nullable": true
                          },
                          "uniprot_names": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "uniprot_full_names": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "uniprot_ids": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            },
                            "nullable": true
                          },
                          "MANE_Select": {
                            "type": "boolean",
                            "nullable": true
                          },
                          "organism": {
                            "type": "string"
                          },
                          "source": {
                            "type": "string"
                          },
                          "source_url": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "_id",
                          "organism",
                          "source",
                          "source_url"
                        ],
                        "additionalProperties": false
                      }
                    }
                  ]
                },
                "detection_method": {
                  "type": "string"
                },
                "detection_method_code": {
                  "type": "string"
                },
                "interaction_type": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "enum": [
                      "acetylation reaction",
                      "adp ribosylation reaction",
                      "ampylation reaction",
                      "association",
                      "atpase reaction",
                      "cleavage reaction",
                      "colocalization",
                      "covalent binding",
                      "de-ADP-ribosylation reaction",
                      "deacetylation reaction",
                      "demethylation reaction",
                      "deneddylation reaction",
                      "dephosphorylation reaction",
                      "deubiquitination reaction",
                      "direct interaction",
                      "disulfide bond",
                      "dna cleavage",
                      "enzymatic reaction",
                      "glycosylation reaction",
                      "gtpase reaction",
                      "guanine nucleotide exchange factor reaction",
                      "hydroxylation reaction",
                      "lipid addition",
                      "lipoprotein cleavage reaction",
                      "methylation reaction",
                      "myristoylation reaction",
                      "neddylation reaction",
                      "oxidoreductase activity electron transfer reaction",
                      "palmitoylation reaction",
                      "phosphorylation reaction",
                      "phosphotransfer reaction",
                      "physical association",
                      "proline isomerization  reaction",
                      "protein cleavage",
                      "proximity",
                      "putative self interaction",
                      "rna cleavage",
                      "self interaction",
                      "sumoylation reaction",
                      "transglutamination reaction",
                      "ubiquitination reaction"
                    ]
                  }
                },
                "interaction_type_code": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "confidence_value_biogrid": {
                  "type": "number",
                  "nullable": true
                },
                "confidence_value_intact": {
                  "type": "number",
                  "nullable": true
                },
                "label": {
                  "type": "string"
                },
                "class": {
                  "type": "string"
                },
                "method": {
                  "type": "string"
                },
                "source_url": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "organism": {
                  "type": "string"
                },
                "pmids": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "name": {
                  "type": "string"
                }
              },
              "required": [
                "protein 1",
                "protein 2",
                "detection_method",
                "detection_method_code",
                "interaction_type",
                "interaction_type_code",
                "confidence_value_biogrid",
                "confidence_value_intact",
                "label",
                "class",
                "method",
                "source_url",
                "source",
                "organism",
                "pmids",
                "name"
              ],
              "additionalProperties": false
            }
          }
        }
      }
    },
    "default": {
      "$ref": "#/components/responses/error"
    }
  }
}
```

## Implementation notes

_(none yet)_
