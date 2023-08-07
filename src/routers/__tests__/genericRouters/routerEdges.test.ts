import mock = require('mock-fs')
import { db } from '../../../database'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { configType, schemaConfigFilePath } from '../../../constants'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'

const SCHEMA_CONFIG = `
gene:
  is_a: biological entity
  represented_as: node
  label_in_input: gencode_gene
  db_collection_name: genes
  db_collection_per_chromosome: false
  db_indexes:
    query:
      type: persistent
      fields:
        - chr, gene_type, gene_name
        - gene_name, gene_type
        - gene_type
        - alias[*]
    text:
      type: inverted
      fields: term_name
    coordinates:
      type: zkd
      fields:
        - start, end
  accessible_via:
    name: genes
    description: 'Retrieve gene information. For example: region = chr1:1157520-1158189 or gene_type = miRNA'
    filter_by: _id, chr, gene_name, gene_type
    filter_by_range: start, end
    fuzzy_text_search: gene_name
    return: _id, chr, start, end, gene_id, gene_name, gene_type, source, version, source_url, alias
  properties:
    chr: str
    start: int
    end: int
    gene_name: str
    gene_id: str
    gene_type: str
    alias: array
    source: str
    version: str
    source_url: str

transcript:
  represented_as: node
  label_in_input: gencode_transcript
  db_collection_name: transcripts
  db_collection_per_chromosome: false
  db_indexes:
    query:
      type: persistent
      fields:
        - chr, gene_name, transcript_name, transcript_type
        - gene_name, transcript_name, transcript_type
        - transcript_name, transcript_type
        - transcript_type
    coordinates:
      type: zkd
      fields:
        - start:long,end:long
  accessible_via:
    name: transcripts
    description: 'Retrieve transcript information. For example: region = chr20:9537369-9839076 or transcript_type = protein_coding'
    filter_by: _id, chr, gene_name, transcript_name, transcript_type
    filter_by_range: start, end
    return: _id, chr, start, end, gene_name, transcript_id, transcript_name, transcript_type, source, version, source_url
  properties:
    chr: str
    start: int
    end: int
    gene_name: str
    transcript_name: str
    transcript_id: str
    transcript_type: str
    source: str
    version: str
    source_url: str

transcribed to:
  represented_as: edge
  is_a: related to at instance level
  domain: gene
  range: transcript
  label_in_input: transcribed_to
  label_as_edge: TRANSCRIBED_TO
  db_collection_name: genes_transcripts
  relationship:
    from: gene
    to: transcript
  accessible_via:
    name: genes_transcripts
    description: 'Retrieve edge data between the relationship of genes and transcripts.'
    return: _id, source, version, source_url
  properties:
    source: str
    version: str
    source_url: str

protein:
  represented_as: node
  label_in_input: UniProtKB_protein
  db_collection_name: proteins
  db_collection_per_chromosome: false
  db_indexes:
    query:
      type: persistent
      fields:
        - name
        - dbxrefs[*]
    text:
      type: inverted
      fields: dbxrefs[*]
  accessible_via:
    name: proteins
    description: 'Retrieve protein data. Example: name = 1433B_HUMAN'
    filter_by: _id, name
    fuzzy_text_search: dbxrefs[*]
    return: _id, name, source, source_url, dbxrefs
  properties:
    name: str
    dbxrefs: array
    source: str
    source_url: str

translates to:
  is_a: related to at instance level
  represented_as: edge
  label_in_input: UniProtKB_Translates_To
  label_as_edge: Translates_to
  db_collection_name: transcripts_proteins
  db_collection_per_chromosome: false
  relationship:
    from: transcript
    to: protein
`

describe('routerEdges', () => {
  let routerEdge: RouterEdges
  let secondaryRouter: RouterEdges
  let schema: Record<string, configType>
  let mockQuery: any

  beforeEach(() => {
    const config: Record<string, string> = {}
    config[schemaConfigFilePath] = SCHEMA_CONFIG
    mock(config)

    schema = loadSchemaConfig()
    const schemaObj = schema['transcribed to']
    const secondarySchemaObj = schema['translates to']

    secondaryRouter = new RouterEdges(secondarySchemaObj)
    routerEdge = new RouterEdges(schemaObj, secondaryRouter)

    class DB {
      public all (): any[] {
        return ['records']
      }
    }

    const mockPromise = new Promise<any>((resolve) => {
      resolve(new DB())
    })

    mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)
  })

  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('loads collections info correctly', () => {
      expect(routerEdge.secondaryRouter).toBe(secondaryRouter)
      expect(routerEdge.edgeCollection).toBe('genes_transcripts')
      expect(routerEdge.secondaryEdgeCollection).toBe('transcripts_proteins')
      expect(routerEdge.sourceSchema).toEqual(schema.gene)
      expect(routerEdge.targetSchema).toEqual(schema.transcript)
      expect(routerEdge.sourceReturnStatements).toEqual(new RouterFilterBy(schema.gene).dbReturnStatements)
      expect(routerEdge.targetReturnStatements).toEqual(new RouterFilterBy(schema.transcript).dbReturnStatements)
      expect(routerEdge.sourceSchemaCollection).toBe('genes')
      expect(routerEdge.targetSchemaCollection).toBe('transcripts')
    })
  })

  describe('filterStatements', () => {
    test('generates adequate AQL filter statement', () => {
      const input = {
        region: 'chr1:12345-54321',
        gene_type: 'coding',
        page: 1
      }

      const stats = routerEdge.filterStatements(input, routerEdge.sourceSchema)
      expect(stats).toEqual("record.gene_type == 'coding' and record.chr == 'chr1' and record['start:long'] >= 12345 and record['end:long'] <= 54321")
    })
  })

  describe('sortByStatement', () => {
    test('generates adequate AQL sort statements', () => {
      expect(routerEdge.sortByStatement('')).toEqual('')
      expect(routerEdge.sortByStatement('chr')).toEqual('SORT record[\'chr\']')
    })
  })

  describe('getTargetsByID', () => {
    let transcripts: any

    beforeEach(async () => {
      transcripts = await routerEdge.getTargetsByID('gene_123', 0, 'chr')
    })

    test('queries the correct edge collection', async () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
    })

    test('filters by target elements by ID', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from == 'genes/gene_123'"))
    })

    test('adds correct sort parameter', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
    })

    test('adds correct pagination', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
    })

    test('returns source records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._to)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { ${routerEdge.targetReturnStatements} }`))
    })

    test('returns records', () => {
      expect(transcripts).toEqual(['records'])
    })
  })

  describe('getTargets', () => {
    let transcripts: any
    let input: Record<string, string | number>

    beforeEach(async () => {
      input = {
        region: 'chr1:123-321',
        gene_type: 'noncoding',
        page: 0
      }
      transcripts = await routerEdge.getTargets(input, 'chr')
    })

    test('filters correct sources from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.filterStatements(input, routerEdge.sourceSchema)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
    })

    test('filters targets based on sources query', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN sources'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._to)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { ${routerEdge.targetReturnStatements} }`))
    })

    test('returns records', () => {
      expect(transcripts).toEqual(['records'])
    })
  })

  describe('getSourcesByID', () => {
    let genes: any

    beforeEach(async () => {
      genes = await routerEdge.getSourcesByID('transcript_321', 0, 'chr')
    })

    test('queries the correct edge collection', async () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
    })

    test('filters by target elements by ID', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'transcripts/transcript_321'"))
    })

    test('adds correct sort parameter', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
    })

    test('adds correct pagination', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
    })

    test('returns source records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._from)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { ${routerEdge.sourceReturnStatements} }`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getSources', () => {
    let genes: any
    let input: Record<string, string | number>

    beforeEach(async () => {
      input = {
        region: 'chr1:123-321',
        gene_type: 'noncoding',
        page: 0
      }
      genes = await routerEdge.getSources(input, 'chr')
    })

    test('filters correct targets from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.filterStatements(input, routerEdge.targetSchema)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
    })

    test('filters sources based on targets query', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN targets'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._from)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { ${routerEdge.sourceReturnStatements} }`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getSecondaryTargetsByID', () => {
    let proteins: any

    beforeEach(async () => {
      proteins = await routerEdge.getSecondaryTargetsByID('gene_123', 0, 'chr')
    })

    test('filters correct targets from primary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from == 'genes/gene_123'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._to'))
    })

    test('filters targets from secondary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN primaryTargets'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._to)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${secondaryRouter.targetReturnStatements}}`))
    })

    test('returns records', () => {
      expect(proteins).toEqual(['records'])
    })
  })

  describe('getSecondaryTargets', () => {
    let proteins: any
    let input: Record<string, string | number>

    beforeEach(async () => {
      input = {
        gene_type: 'miRNA',
        page: 0
      }

      proteins = await routerEdge.getSecondaryTargets(input, 'chr')
    })

    test('filters correct sources from primary collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.filterStatements(input, routerEdge.sourceSchema)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
    })

    test('filters sources from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN primarySources'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._to'))
    })

    test('filters targets from secondary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN primaryTargets'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._to)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${secondaryRouter.targetReturnStatements}}`))
    })

    test('returns records', () => {
      expect(proteins).toEqual(['records'])
    })
  })

  describe('getSecondarySourcesByID', () => {
    let genes: any

    beforeEach(async () => {
      genes = await routerEdge.getSecondarySourcesByID('protein_123', 0, 'chr')
    })

    test('filters correct sources from secondary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'proteins/protein_123'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._from'))
    })

    test('filters sources from primary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN secondarySources'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._from)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements}}`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getSecondarySources', () => {
    let genes: any
    let input: Record<string, string | number>

    beforeEach(async () => {
      input = {
        dbxrefs: 'CDT',
        page: 0
      }

      genes = await routerEdge.getSecondarySources(input, 'chr')
    })

    test('filters correct targets from secondary collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.filterStatements(input, secondaryRouter.targetSchema)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
    })

    test('filters sources from secondary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN secondaryTargets'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._from'))
    })

    test('filters sources from primary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN secondarySources'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DOCUMENT(record._from)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements}}`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })
})
