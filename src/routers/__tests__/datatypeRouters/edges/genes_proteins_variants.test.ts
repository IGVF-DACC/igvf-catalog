import { genesProteinsVariants } from '../../../datatypeRouters/edges/genes_proteins_variants'
import * as dbModule from '../../../../database'

jest.mock('../../../../database')

describe('genesProteinsVariants.variantsFromGeneProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants related to genes/proteins matched by a search term', async () => {
    const mainQueryResult = [
      {
        related: [
          {
            gene: 'genes/ENSG1',
            sources: [
              { label: 'eQTL', source: 'GTEx', neg_log10_pvalue: 5.2, biological_context: 'liver', name: 'acts on', files_filesets: 'files_filesets/FILESET1' }
            ]
          }
        ],
        sequence_variant: {
          _id: 'NC_000001.11:69433:A:G',
          chr: 'chr1',
          pos: 69433,
          rsid: ['rs123'],
          ref: 'A',
          alt: 'G',
          spdi: 'NC_000001.11:69433:A:G',
          hgvs: 'NC_000001.11:g.69434A>G',
          ca_id: 'CA123456'
        }
      }
    ]

    const verboseGeneResult = [
      { _id: 'genes/ENSG1', chr: 'chr1', gene_id: 'ENSG1', hgnc: 'HGNC:1', name: 'GENE1', organism: 'Homo sapiens', files_filesets: null }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG1']) } as any) // geneIds
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // proteinIds
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mainQueryResult) } as any) // main query
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(verboseGeneResult) } as any) // verboseItems genes
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any) // verboseItems proteins

    const input = { query: 'GENE1', page: 0 }
    const result: any = await genesProteinsVariants.variantsFromGeneProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result[0].related[0].gene).toEqual(verboseGeneResult[0])
    expect(result[0].sequence_variant._id).toBe('NC_000001.11:69433:A:G')
    expect(dbModule.db.query).toHaveBeenCalledTimes(5)
  })
})

describe('genesProteinsVariants.genesProteinsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes/proteins related to a variant', async () => {
    const mainQueryResult = [
      {
        sequence_variant: {
          _id: 'NC_000001.11:69433:A:G',
          chr: 'chr1',
          pos: 69433,
          rsid: ['rs123'],
          ref: 'A',
          alt: 'G',
          spdi: 'NC_000001.11:69433:A:G',
          hgvs: 'NC_000001.11:g.69434A>G',
          ca_id: 'CA123456'
        },
        related: [
          { protein: 'proteins/ENSP1', sources: [{ motif: null, source: 'HOCOMOCOv11', name: 'binds', files_filesets: 'files_filesets/FILESET2' }] }
        ]
      }
    ]

    const verboseProteinResult = [
      { _id: 'proteins/ENSP1', name: 'PROT1', uniprot_names: ['P12345'], files_filesets: null }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mainQueryResult) } as any) // main query
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // verboseItems genes
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(verboseProteinResult) } as any) // verboseItems proteins
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { variant_id: 'NC_000001.11:69433:A:G', page: 0 }
    const result: any = await genesProteinsVariants.genesProteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result[0].related[0].protein).toEqual(verboseProteinResult[0])
    expect(dbModule.db.query).toHaveBeenCalledTimes(3)
  })
})

describe('genesProteinsVariants.genesProteinsGenesProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes/proteins related to genes/proteins matched by a search term', async () => {
    const finalResult = [
      {
        protein: { _id: 'ENSP1', name: 'PROT1', uniprot_names: ['P1'], files_filesets: null },
        related: [{ _id: 'ENSP2', name: 'PROT2', uniprot_names: ['P2'], files_filesets: null }]
      },
      {
        gene: { _id: 'ENSG1', chr: 'chr1', gene_id: 'ENSG1', hgnc: 'HGNC:1', name: 'GENE1', organism: 'Homo sapiens', files_filesets: null },
        related: [{ _id: 'ENSG2', chr: 'chr2', gene_id: 'ENSG2', hgnc: null, name: 'GENE2', organism: 'Homo sapiens', files_filesets: null }]
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG1']) } as any) // geneIds
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(finalResult) } as any) // genesProteinsFromGenes

    const input = { query: 'GENE1', page: 0 }
    const result = await genesProteinsVariants.genesProteinsGenesProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(finalResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns an empty array when no genes or proteins match the search term', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // geneIds
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // proteinIds

    const input = { query: 'UNKNOWN', page: 0 }
    const result = await genesProteinsVariants.genesProteinsGenesProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })
})
