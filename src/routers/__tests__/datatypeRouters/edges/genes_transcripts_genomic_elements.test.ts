import { genesTranscriptsGenomicElementsRouters } from '../../../datatypeRouters/edges/genes_transcripts_genomic_elements'
import { edgeRouters } from '../../../datatypeRouters/edges/_all'
import { CATALOG_ENDPOINTS } from '../../../../catalogEndpoints'
import { db } from '../../../../database'

jest.mock('../../../../database')

const call = async (input: Record<string, unknown>): Promise<any> => await genesTranscriptsGenomicElementsRouters.genesTranscriptsGenomicElements({ input, ctx: {}, type: 'query', path: '', rawInput: input })

beforeEach(() => {
  jest.clearAllMocks()
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
})

it('filters through the source gene-transcript relationship and independently selects a peak', async () => {
  await call({ gene_id: 'genes/ENSG00000123685.2', transcript_id: 'ENST00000243440.3', genomic_element_id: 'genomic_elements/ATAC_chr1_10002_10616_GRCh38_IGVFFI0911IUZS' })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('FOR record IN genes_transcripts_genomic_elements')
  expect(query).toContain('LET relationship = DOCUMENT(record._from)')
  expect(query).toContain('relationship._from == @gene_id')
  expect(query).toContain('relationship._to == @transcript_id')
  expect(query).toContain('record._to == @genomic_element_id')
  expect(vars).toMatchObject({ gene_id: 'genes/ENSG00000123685', transcript_id: 'transcripts/ENST00000243440', genomic_element_id: 'genomic_elements/ATAC_chr1_10002_10616_GRCh38_IGVFFI0911IUZS' })
})

it('uses bound values for names, metadata, numeric filters, and pagination', async () => {
  await call({ gene_name: "BATF3' OR true", biological_context: 'T cells', biosample_term: 'CL_0000909', files_fileset: 'files_filesets/IGVFFI2320OTYL', significant: 'false', log2FC: 'lte:-1.5', p_value_adj: 'lt:0.05', base_mean: 'gte:10', page: 2, limit: 1000 })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).not.toContain("BATF3' OR true")
  expect(query).toContain('DOCUMENT(relationship._from).name == @gene_name')
  expect(query).toContain('record.log2FC != null AND record.log2FC <= @log2FC')
  expect(query).toContain('record.p_value_adj != null AND record.p_value_adj < @p_value_adj')
  expect(query).toContain('record.significant == @significant')
  expect(vars).toMatchObject({ gene_name: "BATF3' OR true", biological_context: 'T cells', biosample_term: 'ontology_terms/CL_0000909', files_fileset: 'files_filesets/IGVFFI2320OTYL', significant: false, log2FC: -1.5, p_value_adj: 0.05, base_mean: 10, limit: 500, offset: 1000 })
})

it('matches half-open peak overlap before edge pagination, including intervals beginning at zero', async () => {
  await call({ accessible_region: 'chr1:0-10616', significant: 'true' })
  const [query, vars] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('peak.chr == @chrom AND peak.start < @end AND peak.end > @start')
  expect(query).toContain('record._to IN targetIDs')
  expect(query.indexOf('record._to IN targetIDs')).toBeLessThan(query.indexOf('LIMIT @offset'))
  expect(vars).toMatchObject({ chrom: 'chr1', start: 0, end: 10616, significant: true })
})

it('expands all three nodes in verbose mode and preserves full document handles', async () => {
  await call({ method: 'ATAC-seq', verbose: 'true' })
  const [query] = (db.query as jest.Mock).mock.calls[0]
  expect(query).toContain('DOCUMENT(relationship._from)')
  expect(query).toContain('DOCUMENT(relationship._to)')
  expect(query).toContain('DOCUMENT(record._to)')
  expect(query).toContain("'_id': node['_id']")
  expect(query).toContain('gene_transcript: record._from')
  expect(query).toContain('inverse_name: record.inverse_name')
})

const row = {
  _id: 'genes_transcripts_genomic_elements/effect',
  gene_transcript: 'genes_transcripts/ENSG00000123685_ENST00000243440',
  gene: 'genes/ENSG00000123685',
  transcript: 'transcripts/ENST00000243440',
  accessible_genomic_element: 'genomic_elements/ATAC_chr1_10002_10616_GRCh38_IGVFFI0911IUZS',
  log2FC: null,
  standard_error: null,
  base_mean: 0,
  p_value: null,
  p_value_adj: null,
  neg_log10_pvalue: null,
  neg_log10_pvalue_adj: null,
  significant: false,
  name: 'modulates accessibility of',
  inverse_name: 'accessibility modulated by',
  label: 'gene overexpression effect on chromatin accessibility',
  class: 'observed data',
  method: 'ATAC-seq',
  perturbation: 'ORF overexpression',
  source: 'IGVF',
  source_url: 'https://data.igvf.org/tabular-files/IGVFFI0911IUZS/',
  files_filesets: 'files_filesets/IGVFFI0911IUZS',
  biological_context: 'T cell',
  biosample_term: 'ontology_terms/CL_0000909',
  treatments_term_ids: null
}

it('returns node handles and nullable DESeq2 results without dropping metadata', async () => {
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([row]) } as any)
  expect(await call({ files_fileset: 'IGVFFI0911IUZS' })).toEqual([row])
  expect((db.query as jest.Mock).mock.calls[0][0]).toContain('accessible_genomic_element: record._to')
})

it('accepts expanded nodes and missing linked documents', async () => {
  const expanded = { ...row, gene: { _id: 'genes/ENSG00000123685', name: 'BATF3' }, transcript: null, accessible_genomic_element: { _id: row.accessible_genomic_element, chr: 'chr1', start: 10002, end: 10616, name: 'peak', source_annotation: null, type: 'accessible dna elements', source: 'IGVF', source_url: row.source_url } }
  jest.spyOn(db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([expanded]) } as any)
  expect(await call({ method: 'ATAC-seq', verbose: 'true' })).toEqual([expanded])
})

it.each([
  {}, { significant: 'true' }, { gene_id: ' ' }, { method: 'MORF screen' },
  { method: 'ATAC-seq', page: -1 }, { method: 'ATAC-seq', page: 0.5 },
  { method: 'ATAC-seq', limit: 0 }, { method: 'ATAC-seq', limit: 1.5 },
  { accessible_region: 'chr1:10-10' }, { accessible_region: 'chr1:20-10' },
  { accessible_region: 'chr1:-1-10' }, { accessible_region: 'chr1:0-10 RETURN 1' },
  { method: 'ATAC-seq', p_value_adj: 'lt:0 RETURN 1' },
  { method: 'ATAC-seq', log2FC: 'constructor:1' },
  { method: 'ATAC-seq', log2FC: 'gt:NaN' }, { method: 'ATAC-seq', log2FC: 'gt:' },
  { method: 'ATAC-seq', log2FC: '1:2:3' }, { method: 'ATAC-seq', base_mean: 'Infinity' }
])('rejects invalid or unbounded input without querying the database: %j', async input => {
  await expect(call(input)).rejects.toThrow()
  expect(db.query).not.toHaveBeenCalled()
})

it('registers the procedure in the app and IGVF OpenAPI category', () => {
  expect(edgeRouters.genesTranscriptsGenomicElements).toBe(genesTranscriptsGenomicElementsRouters.genesTranscriptsGenomicElements)
  expect(CATALOG_ENDPOINTS.find(e => e.path === '/genes/transcripts/genomic-elements')?.tag).toBe('IGVF Data')
})
