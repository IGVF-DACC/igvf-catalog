import mock = require('mock-fs')
import { db } from '../../../database'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { configType, schemaConfigFilePath } from '../../../constants'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import * as helpers from '../../../routers/datatypeRouters/_helpers'

const SCHEMA_CONFIG = `
study:
  represented_as: node
  is_a: ontology class
  label_in_input: gwas_study
  db_collection_name: studies
  db_collection_per_chromosome: false
  accessible_via:
    name: studies
    description: 'Retrieve GWAS studies associated data'
    return: _id, pmid
  properties:
    ancestry_initial: str
    ancestry_replication: str
    n_cases: str
    n_initial: str
    n_replication: str
    pmid: str

study to variant:
  represented_as: edge
  is_a: ontology class
  label_in_input: gwas_study_variants
  db_collection_name: studies_variants
  db_collection_per_chromosome: false
  relationship:
    from: study
    to: sequence variant
  accessible_via:
    name: study/variants
    description: 'Retrieve relationship data between GWAS studies and variants'
    filter_by_range: p_val
    return: _to, _from, p_val
  properties:
    lead_chrom: str
    lead_pos: str
    lead_ref: str
    lead_alt: str
    direction: str
    p_val: str

study to variant to phenotype:
  represented_as: edge
  is_a: ontology class
  label_in_input: gwas_study_variants_phenotypes
  db_collection_name: studies_variants_phenotypes
  db_collection_per_chromosome: false
  relationship:
    from: study to variant
    to: ontology term
  accessible_via:
    name: study/variants/phenotypes
    description: 'Retrieve relationship data between phenotypes and GWAS studies associated with variants'
    filter_by: source
    return: _to, _from, source
  properties:
    equivalent_ontology_term: str
    source: str
    version': str

ontology term:
  is_a: ontology class
  represented_as: node
  label_in_input: ontology_term
  db_collection_name: ontology_terms
  accessible_via:
    name: ontology_terms
    filter_by: _id, term_id, term_name, source
    fuzzy_text_search: term_name
    return: _id, uri, term_id, term_name, description, source
  properties:
    uri: str
    term_id: str
    term_name: str
    description: str
    synonyms: obj
    source: str
    subontology: str
    subset: str

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
  accessible_via:
    name: transcripts_proteins
    description: 'Retrieve edge data between the relationship of proteins and transcripts.'
    filter_by: _id
    return: _id, source
  properties:
    source: str

topld:
  is_a: related to at instance level
  represented_as: edge
  label_in_input: topld_linkage_disequilibrium
  label_as_edge: topld_linkage_disquilibrium
  db_collection_name: variants_variants
  db_collection_per_chromosome: false
  relationship:
    from: sequence variant
    to: sequence variant
  accessible_via:
    name: variants_variants_ld
    description: 'Retrieve variant correlation data. Example: r2 = gt:0.8, d_prime = lte:0.5, ancestry = SAS'
    filter_by: r2, d_prime, ancestry, label
    filter_by_range: pos
    return: _id, chr, ancestry, d_prime, label, r2, variant_1_base_pair, variant_1_rsid, variant_2_base_pair, variant_2_rsid
  properties:
    chr: str
    ancestry: str
    negated: boolean
    variant_1_base_pair: str
    variant_2_base_pair: str
    variant_1_rsid: str
    variant_2_rsid: str
    r2: int
    d_prime: int
    label: str
    source: str
    source_url: str

sequence variant:
  represented_as: node
  label_in_input: favor
  db_collection_name: variants
  db_collection_per_chromosome: false
  accessible_via:
    name: variants
    description: 'Retrieve variant data. For example: region = chr1:1157520-1158189 or funseq_description = noncoding or rsid = rs2045642915'
    filter_by: _id
    filter_by_range: pos
    return: _id, chr, pos, rsid, ref, alt, qual, filter, format, source, source_url, annotations
  properties:
    chr: str
    pos: int
    rsid: array
    ref: str
    alt: str
    qual: str
    filter: str
    format: str
    source: str
    source_url: str
    annotations: obj
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
        chr: 'chr1',
        intersect: 'start-end:12345-54321',
        gene_type: 'coding',
        page: 1
      }

      const stats = routerEdge.filterStatements(input, routerEdge.sourceSchema)
      expect(stats).toEqual("record.chr == 'chr1' and ((record['end:long'] >= 12345 AND record['end:long'] <= 54321) OR (record['start:long'] >= 12345 AND record['start:long'] <= 54321) OR (record['end:long'] >= 12345 AND record['start:long'] <= 54321)) and record.gene_type == 'coding'")
    })
  })

  describe('sortByStatement', () => {
    test('generates adequate AQL sort statements', () => {
      expect(routerEdge.sortByStatement('')).toEqual('')
      expect(routerEdge.sortByStatement('chr')).toEqual('SORT record[\'chr\']')
    })
  })

  describe('getBidirectionalByID', () => {
    let varCorrelation: any
    let router: RouterEdges

    describe('not verbose', () => {
      beforeEach(async () => {
        const topld = schema.topld
        router = new RouterEdges(topld)

        const input = {
          variant_id: 'variant_123',
          r2: 'gte:0.1',
          ancestry: 'SAS',
          page: 0,
          verbose: 'false'
        }

        varCorrelation = await router.getBidirectionalByID(input, 'variant_id', 0, '_key', false)
      })

      test('filters correct sources from edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN variants_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER (record._from == 'variants/variant_123' OR record._to == 'variants/variant_123')  AND record.r2 == 'gte:0.1' and record.ancestry == 'SAS'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['_key']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${router.dbReturnStatements}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': otherRecordKey"))
      })

      test('returns records', () => {
        expect(varCorrelation).toEqual(['records'])
      })
    })

    describe('verbose', () => {
      beforeEach(async () => {
        const topld = schema.topld
        router = new RouterEdges(topld)

        const input = {
          variant_id: 'variant_123',
          r2: 'gte:0.1',
          ancestry: 'SAS',
          page: 0,
          verbose: 'false'
        }

        varCorrelation = await router.getBidirectionalByID(input, 'variant_id', 0, '_key', true)
      })

      test('filters correct sources from edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN variants_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER (record._from == 'variants/variant_123' OR record._to == 'variants/variant_123')  AND record.r2 == 'gte:0.1' and record.ancestry == 'SAS'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['_key']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${router.dbReturnStatements}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': ("))
      })

      test('filters targets based on sources query', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord in variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == otherRecordKey'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${router.sourceReturnStatements.replaceAll('record', 'otherRecord')}}`))
      })

      test('returns records', () => {
        expect(varCorrelation).toEqual(['records'])
      })
    })
  })

  describe('getCompleteBidirectionalByID', () => {
    let varCorrelation: any
    let router: RouterEdges

    beforeEach(async () => {
      const topld = schema.topld
      router = new RouterEdges(topld)

      const input = {
        variant_id: 'variant_123',
        r2: 'gte:0.1',
        ancestry: 'SAS',
        page: 0
      }

      varCorrelation = await router.getCompleteBidirectionalByID(input, 'variant_id', 0, '_key')
    })

    test('filters correct sources from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN variants_variants'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER (record._from == 'variants/variant_123' OR record._to == 'variants/variant_123')  AND record.r2 == 'gte:0.1' and record.ancestry == 'SAS'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['_key']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('[record._from == \'variants/variant_123\' ? \'sequence variant\' : \'sequence variant\']: UNSET(DOCUMENT(record._from == \'variants/variant_123\' ? record._to : record._from), \'_rev\', \'_id\')'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(router.dbReturnStatements))
    })

    test('returns records', () => {
      expect(varCorrelation).toEqual(['records'])
    })
  })

  describe('getTargetsByID', () => {
    let transcripts: any

    describe('no verbose', () => {
      beforeEach(async () => {
        transcripts = await routerEdge.getTargetsByID('gene_123', 0, 'chr', false)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': record._to,"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("_id: record._key, 'source': record['source'], 'version': record['version'], 'source_url': record['source_url']"))
      })

      test('returns records', () => {
        expect(transcripts).toEqual(['records'])
      })
    })

    describe('verbose', () => {
      beforeEach(async () => {
        transcripts = await routerEdge.getTargetsByID('gene_123', 0, 'chr', true)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("_id: record._key, 'source': record['source'], 'version': record['version'], 'source_url': record['source_url']"))
      })

      test('returns records', () => {
        expect(transcripts).toEqual(['records'])
      })
    })
  })

  describe('getTargets', () => {
    let transcripts: any
    let input: Record<string, string | number>

    describe('no verbose', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        transcripts = await routerEdge.getTargets(input, 'chr', false)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': record._to"))
      })

      test('returns records', () => {
        expect(transcripts).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        transcripts = await routerEdge.getTargets(input, 'chr', true)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("_id: record._key, 'source': record['source'], 'version': record['version'], 'source_url': record['source_url']"))
      })

      test('returns records', () => {
        expect(transcripts).toEqual(['records'])
      })
    })
  })

  describe('getTargetAndEdgeSet', () => {
    let transcripts: any

    beforeEach(async () => {
      transcripts = await routerEdge.getTargetAndEdgeSet('node_id', "'customField': record._key", "'customField': record._key", 0)
    })

    test('filters correct sources from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from == 'node_id'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT record._to'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LET sourceReturn = DOCUMENT(record._from)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LET targetReturn = DOCUMENT(record._to)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
    })

    test('returns records', () => {
      expect(transcripts).toEqual(['records'])
    })
  })

  describe('getSourceAndEdgeSet', () => {
    let transcripts: any

    beforeEach(async () => {
      transcripts = await routerEdge.getSourceAndEdgeSet(['id1', 'id2'], "{'customField': record._key}", "{'customField': record._key}", 0)
    })

    test('filters correct sources from edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to IN ['id1','id2']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT record._from'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LET sourceReturn = DOCUMENT(record._from)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LET targetReturn = DOCUMENT(record._to)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
    })

    test('returns records', () => {
      expect(transcripts).toEqual(['records'])
    })
  })

  describe('getSourcesByID', () => {
    let genes: any

    describe('no verbose', () => {
      beforeEach(async () => {
        genes = await routerEdge.getSourcesByID('transcript_321', 0, 'chr', false)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': record._from"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        genes = await routerEdge.getSourcesByID('transcript_321', 0, 'chr', true)
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN genes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })
  })

  describe('getSources', () => {
    let genes: any
    let input: Record<string, string | number>

    describe('no verbose', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        genes = await routerEdge.getSources(input, 'chr', false, '')
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': record._from"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        genes = await routerEdge.getSources(input, 'chr', true, '')
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
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN genes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })
  })

  describe('getSecondaryTargetIDsFromIDs', () => {
    let proteins: any

    beforeEach(async () => {
      proteins = await routerEdge.getSecondaryTargetIDsFromIDs(['gene_123', 'gene_321'])
    })

    test('filters correct targets from primary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from IN ['gene_123','gene_321']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._to'))
    })

    test('filters targets from secondary edge collection', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN primaryTargets'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT DOCUMENT(record._to)'))
    })

    test('returns only IDs', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
    })

    test('returns records', () => {
      expect(proteins).toEqual(['records'])
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
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT DOCUMENT(record._to)'))
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
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT DOCUMENT(record._to)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${secondaryRouter.targetReturnStatements}}`))
    })

    test('returns records', () => {
      expect(proteins).toEqual(['records'])
    })
  })

  describe('getPrimaryTargetFromHyperEdgeByID', () => {
    let variants: any

    describe('no verbose', () => {
      beforeEach(async () => {
        const schemaObj = schema['study to variant']
        const secondarySchemaObj = schema['study to variant to phenotype']

        routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
        variants = await routerEdge.getPrimaryTargetFromHyperEdgeByID('phenotype_123', 0, 'chr', 'customFilter == true', false)
      })

      test('filters correct sources from secondary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants_phenotypes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'ontology_terms/phenotype_123'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN PARSE_IDENTIFIER(record._from).key'))
      })

      test('filters correct sources from primary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._key IN secondarySources and customFilter == true'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': record._to,"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(variants).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        const schemaObj = schema['study to variant']
        const secondarySchemaObj = schema['study to variant to phenotype']

        routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
        variants = await routerEdge.getPrimaryTargetFromHyperEdgeByID('phenotype_123', 0, 'chr', 'customFilter == true', true)
      })

      test('filters correct sources from secondary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants_phenotypes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'ontology_terms/phenotype_123'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN PARSE_IDENTIFIER(record._from).key'))
      })

      test('filters correct sources from primary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._key IN secondarySources and customFilter == true'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(variants).toEqual(['records'])
      })
    })
  })

  describe('getPrimaryTargetFromHyperEdge', () => {
    let variants: any

    describe('with secondary target filters', () => {
      describe('no verbose', () => {
        beforeEach(async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          const input = {
            gene_type: 'miRNA',
            page: 0
          }

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
          variants = await routerEdge.getPrimaryTargetsFromHyperEdge(input, 0, 'chr', 'customFilter == true', false)
        })

        test('filters correct sources from secondary collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN ontology_terms'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_type == 'miRNA'"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from secondary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants_phenotypes'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN secondaryTargets'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._from'))
        })

        test('filters correct sources from primary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._id IN secondarySources and customFilter == true'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': record._to,"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        })

        test('returns records', () => {
          expect(variants).toEqual(['records'])
        })
      })

      describe('verbose mode', () => {
        beforeEach(async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          const input = {
            gene_type: 'miRNA',
            page: 0
          }

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
          variants = await routerEdge.getPrimaryTargetsFromHyperEdge(input, 0, 'chr', 'customFilter == true', true)
        })

        test('filters correct sources from secondary collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN ontology_terms'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_type == 'miRNA'"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from secondary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants_phenotypes'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN secondaryTargets'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._from'))
        })

        test('filters correct sources from primary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._id IN secondarySources and customFilter == true'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': ("))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN variants'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        })

        test('returns records', () => {
          expect(variants).toEqual(['records'])
        })
      })
    })

    describe('without secondary target filters', () => {
      describe('without custom filters', () => {
        test('raises execption', async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

          try {
            await routerEdge.getPrimaryTargetsFromHyperEdge({}, 0, 'chr')
          } catch (e: any) {
            if (e instanceof Error) {
              expect(e.message).toBe('At least one property must be defined.')
            }
          }
        })
      })

      describe('with custom filters', () => {
        describe('no verbose', () => {
          beforeEach(async () => {
            const schemaObj = schema['study to variant']
            const secondarySchemaObj = schema['study to variant to phenotype']

            const input = {}

            routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
            variants = await routerEdge.getPrimaryTargetsFromHyperEdge(input, 0, 'chr', 'customFilter == true', false)
          })

          test('filters correct sources from primary target collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER customFilter == true'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': record._to,"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
          })

          test('returns records', () => {
            expect(variants).toEqual(['records'])
          })
        })

        describe('verbose mode', () => {
          beforeEach(async () => {
            const schemaObj = schema['study to variant']
            const secondarySchemaObj = schema['study to variant to phenotype']

            const input = {}

            routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
            variants = await routerEdge.getPrimaryTargetsFromHyperEdge(input, 0, 'chr', 'customFilter == true', true)
          })

          test('filters correct sources from primary target collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER customFilter == true'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'sequence variant': ("))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN variants'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
          })

          test('returns records', () => {
            expect(variants).toEqual(['records'])
          })
        })
      })
    })
  })

  describe('getSecondaryTargetFromHyperEdgeByID', () => {
    let phenotypes: any

    describe('no verbose', () => {
      beforeEach(async () => {
        const schemaObj = schema['study to variant']
        const secondarySchemaObj = schema['study to variant to phenotype']

        routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
        phenotypes = await routerEdge.getSecondaryTargetFromHyperEdgeByID('variant_123', 0, 'chr', 'customFilter == true', false)
      })

      test('filters correct sources from primary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'variants/variant_123' and customFilter == true"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN ('))
      })

      test('filters correct sources from secondary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': edgeRecord._to,"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(phenotypes).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        const schemaObj = schema['study to variant']
        const secondarySchemaObj = schema['study to variant to phenotype']

        routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
        phenotypes = await routerEdge.getSecondaryTargetFromHyperEdgeByID('variant_123', 0, 'chr', 'customFilter == true', true)
      })

      test('filters correct sources from primary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to == 'variants/variant_123' and customFilter == true"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN ('))
      })

      test('filters correct sources from secondary edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR targetRecord IN ontology_terms'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge?.secondaryRouter?.targetReturnStatements.replaceAll('record', 'targetRecord') as string}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(phenotypes).toEqual(['records'])
      })
    })
  })

  describe('getSecondaryTargetsFromHyperEdge', () => {
    let phenotypes: any

    describe('with secondary target filters', () => {
      describe('no verbose', () => {
        beforeEach(async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          const input = {
            gene_type: 'miRNA',
            page: 0
          }

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
          phenotypes = await routerEdge.getSecondaryTargetsFromHyperEdge(input, 0, 'chr', '{queryOptions: true}', 'customFilter == true', false)
        })

        test('filters correct sources from primary collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN variants {queryOptions: true}'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_type == 'miRNA'"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from primary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in studies_variants'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN primaryTargets and customFilter == true'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from secondary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': edgeRecord._to,"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        })

        test('returns records', () => {
          expect(phenotypes).toEqual(['records'])
        })
      })

      describe('verbose mode', () => {
        beforeEach(async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          const input = {
            gene_type: 'miRNA',
            page: 0
          }

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
          phenotypes = await routerEdge.getSecondaryTargetsFromHyperEdge(input, 0, 'chr', '{queryOptions: true}', 'customFilter == true', true)
        })

        test('filters correct sources from primary collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN variants {queryOptions: true}'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_type == 'miRNA'"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from primary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in studies_variants'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN primaryTargets and customFilter == true'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._id'))
        })

        test('filters correct sources from secondary edge collection', () => {
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': ("))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR targetRecord IN ontology_terms'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key'))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge?.secondaryRouter?.targetReturnStatements.replaceAll('record', 'targetRecord') as string}}`))
          expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
        })

        test('returns records', () => {
          expect(phenotypes).toEqual(['records'])
        })
      })
    })

    describe('without secondary target filters', () => {
      describe('without custom filters', () => {
        test('raise an exception', async () => {
          const schemaObj = schema['study to variant']
          const secondarySchemaObj = schema['study to variant to phenotype']

          routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

          try {
            await routerEdge.getSecondaryTargetsFromHyperEdge({}, 0, 'chr')
          } catch (e: any) {
            if (e instanceof Error) {
              expect(e.message).toBe('At least one property must be defined.')
            }
          }
        })
      })

      describe('with custom filters', () => {
        describe('no verbose', () => {
          beforeEach(async () => {
            const schemaObj = schema['study to variant']
            const secondarySchemaObj = schema['study to variant to phenotype']

            const input = {}

            routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
            phenotypes = await routerEdge.getSecondaryTargetsFromHyperEdge(input, 0, 'chr', '', 'customFilter == true', false)
          })

          test('filters correct sources from primary edge collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER customFilter == true'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN ('))
          })

          test('filters correct sources from secondary target collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': edgeRecord._to,"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
          })

          test('returns records', () => {
            expect(phenotypes).toEqual(['records'])
          })
        })

        describe('verbose mode', () => {
          beforeEach(async () => {
            const schemaObj = schema['study to variant']
            const secondarySchemaObj = schema['study to variant to phenotype']

            const input = {}

            routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
            phenotypes = await routerEdge.getSecondaryTargetsFromHyperEdge(input, 0, 'chr', '', 'customFilter == true', true)
          })

          test('filters correct sources from primary edge collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN studies_variants'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER customFilter == true'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN ('))
          })

          test('filters correct sources from secondary target collection', () => {
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR edgeRecord IN studies_variants_phenotypes'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER edgeRecord._from == record._id'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'ontology term': ("))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR targetRecord IN ontology_terms'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key'))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge?.secondaryRouter?.targetReturnStatements.replaceAll('record', 'targetRecord') as string}}`))
            expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
          })

          test('returns records', () => {
            expect(phenotypes).toEqual(['records'])
          })
        })
      })
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
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT DOCUMENT(record._from)'))
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
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT DOCUMENT(record._from)'))
    })

    test('returns only return statements from records', () => {
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements}}`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getEdgeObjects', () => {
    let genes: any
    let input: Record<string, string | number>

    beforeEach(async () => {
      input = {
        dbxrefs: 'CDT',
        page: 0
      }
    })

    test('filters correct edge collection', async () => {
      genes = await routerEdge.getEdgeObjects(input)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.getFilterStatements(input)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("RETURN { 'gene': record._from,'transcript': record._to,_id: record._key, 'source': record['source'], 'version': record['version'], 'source_url': record['source_url'] }"))
    })

    test('applies verbose feature correctly', async () => {
      genes = await routerEdge.getEdgeObjects(input, '', true)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FILTER ${routerEdge.getFilterStatements(input)}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == record._from'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.sourceReturnStatements.replaceAll('record', 'otherRecord')}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == record._to'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getTargetSet', () => {
    let genes: any
    let input: string[]

    beforeEach(async () => {
      input = ['id_1', 'id_2']
    })

    test('filters correct edge collection', async () => {
      genes = await routerEdge.getTargetSet(input)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from IN ['id_1','id_2']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('COLLECT source = record._from INTO targetsBySource'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {
          genes: source,
          transcripts: targetsBySource[*].record._to
      }`))
    })

    test('applies verbose feature correctly', async () => {
      genes = await routerEdge.getTargetSet(input, true)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from IN ['id_1','id_2']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('COLLECT source = record._from INTO targetsBySource'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {
          genes: source,
          transcripts: DOCUMENT(targetsBySource[*].record._to)
      }`))
    })

    test('returns records', () => {
      expect(genes).toEqual(['records'])
    })
  })

  describe('getTargetEdgesByTokenTextSearch', () => {
    let genes: any
    let input: Record<string, string | number>

    describe('no verbose', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        genes = await routerEdge.getTargetEdgesByTokenTextSearch(input, 'gene_type', false)
      })

      test('searches correct edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts_fuzzy_search_alias'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("noncoding", "text_en_no_stem") ALL in record.gene_type'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT BM25(record) DESC'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.region == 'chr1:123-321'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': record._to"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })

    describe('verbose mode', () => {
      beforeEach(async () => {
        input = {
          region: 'chr1:123-321',
          gene_type: 'noncoding',
          page: 0
        }
        genes = await routerEdge.getTargetEdgesByTokenTextSearch(input, 'gene_type', true)
      })

      test('searches correct edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts_fuzzy_search_alias'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("noncoding", "text_en_no_stem") ALL in record.gene_type'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT BM25(record) DESC'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.region == 'chr1:123-321'"))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': ("))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${routerEdge.dbReturnStatements}`))
      })

      test('returns records', () => {
        expect(genes).toEqual(['records'])
      })
    })
  })

  describe('getChildrenParents', () => {
    let children: any
    let parents: any

    describe('get parents', () => {
      beforeEach(async () => {
        children = await routerEdge.getChildrenParents('nodeID', 'parents', '_key', 0)
      })

      test('filters correct edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from == \'genes/nodeID\' && details != null'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'term\': details,'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'relationship_type\': record.type || \'null\''))
      })

      test('fetches correct node details', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == record._to'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
      })

      test('returns records', () => {
        expect(children).toEqual(['records'])
      })
    })

    describe('get children', () => {
      beforeEach(async () => {
        parents = await routerEdge.getChildrenParents('nodeID', 'children', '_key', 0)
      })

      test('filters correct edge collection', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to == \'genes/nodeID\' && details != null'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'term\': details,'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'relationship_type\': record.type || \'null\''))
      })

      test('fetches correct node details', () => {
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord IN transcripts'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == record._from'))
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${routerEdge.targetReturnStatements.replaceAll('record', 'otherRecord')}}`))
      })

      test('returns records', () => {
        expect(parents).toEqual(['records'])
      })
    })
  })

  describe('getTargetSetByUnion', () => {
    let mockHelper: any

    beforeEach(() => {
      const response = [
        {
          'sequence variant': {
            _id: 'variants/d3150ff2dd0902361ca538e54b37e3a8276714bbd2d6841b72df0bab696a46bb',
            chr: 'chr20',
            pos: 50292742,
            rsid: [
              'rs17196808'
            ],
            ref: 'C',
            alt: 'T',
            spdi: 'NC_000020.11:50292742:C:T',
            hgvs: 'NC_000020.11:g.50292743C>T'
          },
          related: [
            { transcript: 'transcripts/ENST00000203999', sources: ['variants_transcripts/12345'] },
            { protein: 'proteins/P03372', sources: ['variants_proteins/12345'] }
          ]
        }
      ]

      class DB {
        public all (): any[] {
          return response
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })

      mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const verboseResolver = {
        'transcripts/ENST00000203999': { transcript_name: 'transcript_test' },
        'proteins/P03372': { protein_name: 'protein_test' }
      }
      mockHelper = jest.spyOn(helpers, 'verboseItems').mockReturnValue(Promise.resolve(verboseResolver))
    })

    afterEach(() => {
      mock.restore()
    })

    test('C -> A query matching A', async () => {
      const genes = await routerEdge.getTargetSetByUnion('item-ID', 0)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from == 'item-ID'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`COLLECT from = record._from, to = record._to INTO sources = {${routerEdge.simplifiedDbReturnStatements}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': from"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': { 'transcript': to, 'sources': sources }"))
      expect(genes).not.toBeNull()
    })

    test('C -> B query matching B', async () => {
      const genes = await routerEdge.getTargetSetByUnion('item-ID', 0)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._from == 'item-ID'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`COLLECT from = record._from, to = record._to INTO sources = {${routerEdge.secondaryRouter?.simplifiedDbReturnStatements as string}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': from"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': { 'protein': to, 'sources': sources }"))
      expect(genes).not.toBeNull()
    })

    test('groups A and B, by C', async () => {
      await routerEdge.getTargetSetByUnion('item-ID', 0)
      const sts = new RouterFilterBy(routerEdge.sourceSchema).simplifiedDbReturnStatements.replaceAll('record', 'otherRecord')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in UNION(A, B)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("COLLECT source = record['transcript'] INTO relatedObjs = record.related"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': "))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord in genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == source'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${sts}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': relatedObjs"))
    })

    test('related objects are filled correctly', async () => {
      const genes = await routerEdge.getTargetSetByUnion('item-ID', 0)

      expect(mockHelper).toBeCalledTimes(2)

      const response = [
        {
          'sequence variant': {
            _id: 'variants/d3150ff2dd0902361ca538e54b37e3a8276714bbd2d6841b72df0bab696a46bb',
            chr: 'chr20',
            pos: 50292742,
            rsid: [
              'rs17196808'
            ],
            ref: 'C',
            alt: 'T',
            spdi: 'NC_000020.11:50292742:C:T',
            hgvs: 'NC_000020.11:g.50292743C>T'
          },
          related: [
            { transcript: { transcript_name: 'transcript_test' }, sources: ['variants_transcripts/12345'] },
            { protein: { protein_name: 'protein_test' }, sources: ['variants_proteins/12345'] }
          ]
        }
      ]

      expect(genes).toEqual(response)
    })
  })

  describe('getSourceSetByUnion', () => {
    let mockHelper: any

    beforeEach(() => {
      const response = [
        {
          'sequence variant': {
            _id: 'variants/d3150ff2dd0902361ca538e54b37e3a8276714bbd2d6841b72df0bab696a46bb',
            chr: 'chr20',
            pos: 50292742,
            rsid: [
              'rs17196808'
            ],
            ref: 'C',
            alt: 'T',
            spdi: 'NC_000020.11:50292742:C:T',
            hgvs: 'NC_000020.11:g.50292743C>T'
          },
          related: [
            { transcript: 'transcripts/ENST00000203999', sources: ['variants_transcripts/12345'] },
            { protein: 'proteins/P03372', sources: ['variants_proteins/12345'] }
          ]
        }
      ]

      class DB {
        public all (): any[] {
          return response
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })

      mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const verboseResolver = {
        'transcripts/ENST00000203999': { transcript_name: 'transcript_test' },
        'proteins/P03372': { protein_name: 'protein_test' }
      }
      mockHelper = jest.spyOn(helpers, 'verboseItems').mockReturnValue(Promise.resolve(verboseResolver))
    })

    afterEach(() => {
      mock.restore()
    })

    test('C -> A query matching A', async () => {
      const genes = await routerEdge.getSourceSetByUnion(['item-ID'], 0)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to IN ['item-ID']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`COLLECT from = record._from, to = record._to INTO sources = {${routerEdge.simplifiedDbReturnStatements}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'gene': from"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': { 'transcript': to, 'sources': sources }"))
      expect(genes).not.toBeNull()
    })

    test('C -> B query matching B', async () => {
      const genes = await routerEdge.getSourceSetByUnion(['item-ID'], 0)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record._to IN ['item-ID']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`COLLECT from = record._from, to = record._to INTO sources = {${routerEdge.secondaryRouter?.simplifiedDbReturnStatements as string}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': from"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': { 'protein': to, 'sources': sources }"))
      expect(genes).not.toBeNull()
    })

    test('groups A and B, by C', async () => {
      await routerEdge.getSourceSetByUnion(['item-ID'], 0)
      const sts = new RouterFilterBy(routerEdge.sourceSchema).simplifiedDbReturnStatements.replaceAll('record', 'otherRecord')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record in UNION(A, B)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("COLLECT source = record['transcript'] INTO relatedObjs = record.related"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'transcript': "))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR otherRecord in genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER otherRecord._id == source'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN {${sts}}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("'related': relatedObjs"))
    })

    test('related objects are filled correctly', async () => {
      const genes = await routerEdge.getSourceSetByUnion(['item-ID'], 0)

      expect(mockHelper).toBeCalledTimes(2)

      const response = [
        {
          'sequence variant': {
            _id: 'variants/d3150ff2dd0902361ca538e54b37e3a8276714bbd2d6841b72df0bab696a46bb',
            chr: 'chr20',
            pos: 50292742,
            rsid: [
              'rs17196808'
            ],
            ref: 'C',
            alt: 'T',
            spdi: 'NC_000020.11:50292742:C:T',
            hgvs: 'NC_000020.11:g.50292743C>T'
          },
          related: [
            { transcript: { transcript_name: 'transcript_test' }, sources: ['variants_transcripts/12345'] },
            { protein: { protein_name: 'protein_test' }, sources: ['variants_proteins/12345'] }
          ]
        }
      ]

      expect(genes).toEqual(response)
    })
  })

  describe('getSelfAndTransversalTargetEdges', () => {
    test('A -> B query', async () => {
      const genes = await routerEdge.getSelfAndTransversalTargetEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("LET ids = ['item-ID']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN ids'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._to'))
      expect(genes).not.toBeNull()
    })

    test('(A -> B) -> C query', async () => {
      const genes = await routerEdge.getSelfAndTransversalTargetEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._from IN Bs'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR relatedRecord IN proteins_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER relatedRecord._from == record._to OR relatedRecord._to == record._to'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 12'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT relatedRecord._key'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT(relatedRecord._to == record._to ? relatedRecord._from : relatedRecord._to)'))
      expect(genes).not.toBeNull()
    })

    test('A <-> A query', async () => {
      const genes = await routerEdge.getSelfAndTransversalTargetEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._id IN ids'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR relatedRecord IN genes_genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER relatedRecord._from == record._id or relatedRecord._to == record._id'))
      expect(genes).not.toBeNull()
    })

    test('union query', async () => {
      const genes = await routerEdge.getSelfAndTransversalTargetEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN UNION(C, A)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record'))
      expect(genes).not.toBeNull()
    })
  })

  describe('getSelfAndTransversalSourceEdges', () => {
    test('B -> C query', async () => {
      const genes = await routerEdge.getSelfAndTransversalSourceEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("LET ids = ['item-ID']"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN genes_transcripts'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN ids'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record._from'))
      expect(genes).not.toBeNull()
    })

    test('(A -> B) -> C query', async () => {
      const genes = await routerEdge.getSelfAndTransversalSourceEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN transcripts_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER record._to IN Bs'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT record._from'))
      expect(genes).not.toBeNull()
    })

    test('A <-> A query', async () => {
      const genes = await routerEdge.getSelfAndTransversalSourceEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR relatedRecord IN genes_genes'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER relatedRecord._from == record._id OR relatedRecord._to == record._id'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 12'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT relatedRecord._key'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._id)'))
      expect(genes).not.toBeNull()
    })

    test('C <-> C query', async () => {
      const genes = await routerEdge.getSelfAndTransversalSourceEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR relatedRecord IN proteins_proteins'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER relatedRecord._from == record._id OR relatedRecord._to == record._id'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 12'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT relatedRecord._key'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._id)'))
      expect(genes).not.toBeNull()
    })

    test('union query', async () => {
      const genes = await routerEdge.getSelfAndTransversalTargetEdges(['item-ID'], 0, 'genes_genes', 'proteins_proteins')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR record IN UNION(C, A)'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN record'))
      expect(genes).not.toBeNull()
    })
  })
})
