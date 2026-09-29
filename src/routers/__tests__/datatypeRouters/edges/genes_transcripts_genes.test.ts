import { genesTranscriptsGenesRouters } from '../../../datatypeRouters/edges/genes_transcripts_genes'
import { db } from '../../../../database'
import { CATALOG_ENDPOINTS } from '../../../../catalogEndpoints'

jest.mock('../../../../database')
const call = async (input: Record<string, unknown>): Promise<any> => await genesTranscriptsGenesRouters.genesTranscriptsGenes({ input, ctx: {}, type: 'query', path: '', rawInput: input })

beforeEach(() => {
  jest.clearAllMocks()
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
})

it('queries an edge-to-gene relationship with independent source, transcript and readout filters', async () => {
  await call({ gene_id: 'ENSG00000275700.1', transcript_id: 'ENST00000619387.2', associated_gene_id: 'ENSG00000198846', page: 0 })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('FOR record IN genes_transcripts_genes')
  expect(query).toContain('LET relationship = DOCUMENT(record._from)')
  expect(query).toContain('relationship._from == @gene_id')
  expect(query).toContain('relationship._to == @transcript_id')
  expect(query).toContain('record._to == @associated_gene_id')
  expect(vars).toMatchObject({ gene_id: 'genes/ENSG00000275700', transcript_id: 'transcripts/ENST00000619387', associated_gene_id: 'genes/ENSG00000198846' })
})

it('uses bind parameters for construct strings, numeric filters and pagination', async () => {
  await call({ morf_id: "X' OR true", log2FC: 'gte:1.5', significant: 'true', files_fileset: 'IGVFFI6734IWRB', limit: 1000, page: 2 })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).not.toContain("X' OR true")
  expect(query).toContain('record.log2FC != null AND record.log2FC >= @log2FC')
  expect(query).toContain('record.significant == true')
  expect(vars).toMatchObject({ morf_id: "X' OR true", log2FC: 1.5, files_fileset: 'files_filesets/IGVFFI6734IWRB', limit: 500, offset: 1000 })
})

it('expands all three nodes in verbose mode and exposes the source edge ID', async () => {
  await call({ method: 'MORF screen', verbose: 'true', page: 0 })
  const query = (db.query as jest.Mock).mock.calls[0][0]
  expect(query).toContain('DOCUMENT(relationship._from)')
  expect(query).toContain('DOCUMENT(relationship._to)')
  expect(query).toContain('DOCUMENT(record._to)')
  expect(query).toContain('gene_transcript: record._from')
})

it('returns the relationship ID and all three node handles', async () => {
  const row = {
    _id: 'genes_transcripts_genes/effect',
    gene_transcript: 'genes_transcripts/existing_edge',
    gene: 'genes/ENSG00000275700',
    transcript: 'transcripts/ENST00000619387',
    associated_gene: 'genes/ENSG00000198846',
    morf_id: 'AATF_1',
    transcript_mapping_method: 'supplied ENST',
    standard_error: 0.5,
    log2FC: 1,
    significant: false,
    name: 'modulates expression of',
    label: 'gene overexpression effect on gene expression',
    class: 'observed data',
    method: 'MORF screen',
    source: 'IGVF',
    source_url: 'https://data.igvf.org/tabular-files/IGVFFI6734IWRB/',
    files_filesets: 'files_filesets/IGVFFI6734IWRB',
    biological_context: 'T cell',
    biosample_term: 'ontology_terms/CL_0000625'
  }
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([row]) } as any)
  expect(await call({ morf_id: 'AATF_1', page: 0 })).toEqual([row])
})

it('rejects missing selectors and malformed numeric filters', async () => {
  await expect(call({ page: 0 })).rejects.toThrow('Define at least one')
  for (const log2FC of ['gt:NaN', 'wrong:2', '1:2:3', 'Infinity']) {
    await expect(call({ method: 'MORF screen', log2FC, page: 0 })).rejects.toThrow('must be a number')
  }
  expect(db.query).not.toHaveBeenCalled()
})

it('registers a dedicated IGVF endpoint and leaves genes/genes in its original category', () => {
  expect(CATALOG_ENDPOINTS.find(e => e.path === '/genes/transcripts/genes')?.tag).toBe('IGVF Data')
  expect(CATALOG_ENDPOINTS.find(e => e.path === '/genes/genes')?.tag).toBe('Biological Context Data')
})
