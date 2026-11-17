import { codingVariantsProteinsProteinsRouters } from '../../../datatypeRouters/edges/coding_variants_proteins_proteins'
import * as dbModule from '../../../../database'

jest.mock('../../../../database')

const call = async (procedure: (opts: any) => Promise<any>, input: any): Promise<any> => await procedure({
  input, ctx: {}, type: 'query', path: '', getRawInput: async () => input, signal: undefined, batchIndex: 0
})
const mockRows = (rows: any[]): void => {
  jest.spyOn(dbModule.db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue(rows) } as any)
}
const query = (): string => (dbModule.db.query as jest.Mock).mock.calls[0][0] as string

beforeEach(() => { jest.clearAllMocks(); mockRows([]) })

const edge = {
  _id: 'coding_variants_proteins_proteins/ACSF3_000002a5_IGVFFI2460BBXY',
  coding_variant: 'coding_variants/ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T',
  proteins_proteins: 'proteins_proteins/000002a5a51a3c5a92fc1245bb32701679a33f20b67baff8dfa1a359998dafa4',
  consensus_score: 26.99,
  wt_consensus_score: 311.16,
  log2FC: -3.48,
  molecular_function: 'ontology_terms/GO_0005515',
  method: 'Arrayed semi-qY2H',
  label: 'protein variant effect',
  class: 'observed data',
  source: 'IGVF',
  source_url: 'https://data.igvf.org/tabular-files/IGVFFI2460BBXY',
  name: 'modulates interaction of',
  inverse_name: 'interaction modulated by',
  files_filesets: 'files_filesets/IGVFFI2460BBXY'
}

describe('codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants', () => {
  it('finds PPIs by coding variant identity', async () => {
    mockRows([edge])
    const result = await call(codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants, { coding_variant_name: 'ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T' })
    expect(result).toEqual([edge])
    expect(query()).toContain('FOR record IN coding_variants_proteins_proteins')
    expect(query()).toContain('record._from == cv._id')
    expect(query()).toContain("cv.name == 'ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'")
    expect(query()).not.toContain('record.name ==')
  })

  it('narrows to a specific interaction partner via associated_protein_name', async () => {
    mockRows([edge])
    await call(codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants, { gene_name: 'ACSF3', associated_protein_name: 'KRT40' })
    expect(query()).toContain('FOR associatedProtein IN proteins')
    expect(query()).toContain('(ppi._from == associatedProtein._id OR ppi._to == associatedProtein._id)')
  })

  it('applies a log2FC range filter', async () => {
    await call(codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants, { gene_name: 'ACSF3', log2FC: 'lt:0' })
    expect(query()).toContain("record['log2FC'] < 0")
  })

  it('narrows to a specific interaction partner via associated_dbxrefs', async () => {
    mockRows([edge])
    await call(codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants, { gene_name: 'ACSF3', associated_dbxrefs: 'UniProtKB:Q9BQE5' })
    expect(query()).toContain('FOR associatedProtein IN proteins')
    expect(query()).toContain("'UniProtKB:Q9BQE5' in associatedProtein.dbxrefs[*].id")
  })

  it('rejects a request with no coding variant identifier', async () => {
    await expect(call(codingVariantsProteinsProteinsRouters.proteinsProteinsFromCodingVariants, {})).rejects.toThrow('At least one coding variant parameter must be defined')
    expect(dbModule.db.query).not.toHaveBeenCalled()
  })
})

describe('codingVariantsProteinsProteinsRouters.codingVariantsFromProteinsProteins', () => {
  it('finds coding variants by one protein in the pair', async () => {
    mockRows([edge])
    const result = await call(codingVariantsProteinsProteinsRouters.codingVariantsFromProteinsProteins, { protein_name: 'ACSF3' })
    expect(result).toEqual([edge])
    expect(query()).toContain('FOR protein IN proteins')
    expect(query()).toContain('FOR ppi IN proteins_proteins')
    expect(query()).toContain('(ppi._from == protein._id OR ppi._to == protein._id)')
    expect(query()).toContain('record._to == ppi._id')
  })

  it('finds coding variants by both sides of the interaction', async () => {
    mockRows([edge])
    await call(codingVariantsProteinsProteinsRouters.codingVariantsFromProteinsProteins, { protein_name: 'ACSF3', associated_protein_name: 'KRT40' })
    expect(query()).toContain('FOR protein IN proteins')
    expect(query()).toContain('FOR associatedProtein IN proteins')
    expect(query()).toContain('(ppi._from == protein._id OR ppi._to == protein._id) AND (ppi._from == associatedProtein._id OR ppi._to == associatedProtein._id)')
  })

  it('finds coding variants by dbxrefs', async () => {
    mockRows([edge])
    const result = await call(codingVariantsProteinsProteinsRouters.codingVariantsFromProteinsProteins, { dbxrefs: 'UniProtKB:Q9BQE5' })
    expect(result).toEqual([edge])
    expect(query()).toContain('FOR protein IN proteins')
    expect(query()).toContain("'UniProtKB:Q9BQE5' in protein.dbxrefs[*].id")
  })

  it('rejects a request with no protein identifier', async () => {
    await expect(call(codingVariantsProteinsProteinsRouters.codingVariantsFromProteinsProteins, {})).rejects.toThrow('At least one protein must be defined')
    expect(dbModule.db.query).not.toHaveBeenCalled()
  })
})
