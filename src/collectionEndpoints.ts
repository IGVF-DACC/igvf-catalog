import * as fs from 'fs'
import * as path from 'path'
import { CATALOG_ENDPOINTS } from './catalogEndpoints'

/**
 * Maps every ArangoDB node/edge collection (the keys are exactly the
 * top-level collection names in data/schemas/registry.json, which are
 * always identical to each schema's own db_collection_name - verified by
 * hand against the live schemas) to the public REST API endpoint(s) that
 * serve records from it.
 *
 * Why this exists: some internal tooling (e.g. notebooks that read
 * files_filesets.collections, a list of raw collection names like
 * 'genomic_elements_genes') used to connect directly to ArangoDB to turn a
 * collection name into the matching data. This lets that lookup happen
 * through the public API instead - see GET /collection-endpoints in
 * src/routers/datatypeRouters/collectionEndpoints.ts.
 *
 * This is hand-maintained, not derived, because the endpoint for a
 * collection is not a mechanical transform of its name: 'motifs_proteins'
 * serves two endpoints ('/motifs/proteins' and '/proteins/motifs'); '/qtls'
 * unions three different edge collections into one response; some
 * collections (e.g. 'donors') have no dedicated endpoint at all yet. An
 * endpoints: [] entry means exactly that - there is currently no way to
 * fetch that collection's records from the public API; direct DB access
 * remains the only option for those until a dedicated endpoint is added.
 *
 * Inclusion rule used while building this table (so it can be maintained
 * consistently going forward):
 *   - A node collection maps only to its own dedicated listing endpoint.
 *   - An edge collection maps to every endpoint, in its own dedicated
 *     router file, whose query is driven by a FOR loop directly over that
 *     collection (even if the result is aggregated/reshaped, e.g. a
 *     "-count" or "-summary" endpoint) - not to endpoints that merely join
 *     in one of its records for display (e.g. a verbose-mode lookup).
 *   - An edge collection with no dedicated router file of its own, but
 *     whose data is one of several collections unioned into a shared
 *     multi-collection endpoint (e.g. /qtls, /genes/diseases), maps to
 *     that shared endpoint.
 *   - Deep multi-hop composite endpoints that join 3+ collections with no
 *     single clearly-primary collection (e.g. /genes-proteins/variants,
 *     /genes/coding-variants/scores) are intentionally left out of every
 *     collection's list - they remain discoverable via Swagger's "Bespoke
 *     Endpoints" section.
 *
 * validateCollectionEndpoints() (called at the bottom of this file) checks
 * this table against data/schemas/registry.json and catalogEndpoints.ts at
 * startup, so drift (a new collection added without updating this file, or
 * a typo'd endpoint path) fails loudly instead of silently returning a
 * wrong/incomplete mapping.
 */
export type CollectionType = 'node' | 'edge'

export interface CollectionEndpoint {
  type: CollectionType
  endpoints: string[]
}

export const COLLECTION_ENDPOINTS: Readonly<Record<string, CollectionEndpoint>> = {
  // --- Nodes ---
  coding_variants: { type: 'node', endpoints: ['/coding-variants'] },
  complexes: { type: 'node', endpoints: ['/complexes'] },
  // referenced only via files_filesets._from/_to joins - no dedicated endpoint exists yet
  donors: { type: 'node', endpoints: [] },
  drugs: { type: 'node', endpoints: ['/drugs'] },
  files_filesets: { type: 'node', endpoints: ['/files-filesets'] },
  genes: { type: 'node', endpoints: ['/genes'] },
  genes_structure: { type: 'node', endpoints: ['/genes-structure'] },
  genomic_elements: { type: 'node', endpoints: ['/genomic-elements'] },
  mm_genes: { type: 'node', endpoints: ['/genes'] }, // organism=Mus musculus
  mm_genes_structure: { type: 'node', endpoints: ['/genes-structure'] }, // organism=Mus musculus
  mm_genomic_elements: { type: 'node', endpoints: ['/genomic-elements'] }, // organism=Mus musculus
  mm_transcripts: { type: 'node', endpoints: ['/transcripts'] }, // organism=Mus musculus
  mm_variants: { type: 'node', endpoints: ['/variants'] }, // organism=Mus musculus
  motifs: { type: 'node', endpoints: ['/motifs'] },
  ontology_terms: { type: 'node', endpoints: ['/ontology-terms'] },
  pathways: { type: 'node', endpoints: ['/pathways'] },
  proteins: { type: 'node', endpoints: ['/proteins'] },
  studies: { type: 'node', endpoints: ['/studies'] },
  transcripts: { type: 'node', endpoints: ['/transcripts'] },
  variants: { type: 'node', endpoints: ['/variants', '/variants/freq', '/variants/summary', '/variants/gnomad-alleles'] },

  // --- Edges ---
  coding_variants_phenotypes: {
    type: 'edge',
    endpoints: [
      '/coding-variants/phenotypes',
      '/phenotypes/coding-variants',
      '/coding-variants/phenotypes-count',
      '/variants/phenotypes/score-summary',
      '/coding-variants/phenotypes/score-summary'
    ]
  },
  complexes_proteins: { type: 'edge', endpoints: ['/complexes/proteins', '/proteins/complexes'] },
  complexes_terms: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  diseases_genes: { type: 'edge', endpoints: ['/genes/diseases', '/diseases/genes'] },
  gene_products_terms: { type: 'edge', endpoints: ['/gene-products/go-terms', '/go-terms/gene-products'] },
  genes_biosamples: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  genes_genes: { type: 'edge', endpoints: ['/genes/genes'] },
  // human-mouse ortholog edges (MGI) - no dedicated endpoint exists yet, distinct from mm_genes_mm_genes below
  genes_mm_genes: { type: 'edge', endpoints: [] },
  genes_pathways: { type: 'edge', endpoints: ['/genes/pathways', '/pathways/genes'] },
  genes_transcripts: { type: 'edge', endpoints: ['/genes/transcripts', '/transcripts/genes'] },
  genes_transcripts_genes: { type: 'edge', endpoints: ['/genes/transcripts/genes'] },
  genomic_elements_biosamples: { type: 'edge', endpoints: ['/genomic-elements/biosamples', '/biosamples/genomic-elements'] },
  genomic_elements_genes: {
    type: 'edge',
    endpoints: [
      '/genomic-elements/genes',
      '/genes/genomic-elements',
      '/gene-regulatory-network',
      '/enhancer-gene-predictions',
      '/variants/genomic-elements/genes'
    ]
  },
  genomic_elements_mm_genomic_elements: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  genomic_elements_phenotypes: { type: 'edge', endpoints: ['/genomic-elements/phenotypes', '/phenotypes/genomic-elements'] },
  mm_genes_mm_genes: { type: 'edge', endpoints: ['/genes/genes'] }, // organism=Mus musculus
  mm_genomic_elements_mm_genes: { type: 'edge', endpoints: ['/genomic-elements/genes', '/genes/genomic-elements', '/gene-regulatory-network'] }, // organism=Mus musculus
  mm_transcripts_mm_genes_structure: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  motifs_proteins: { type: 'edge', endpoints: ['/motifs/proteins', '/proteins/motifs'] },
  ontology_terms_ontology_terms: {
    type: 'edge',
    endpoints: [
      '/ontology-terms/{ontology_term_id}/children',
      '/ontology-terms/{ontology_term_id}/parents',
      '/ontology-terms/{ontology_term_id_start}/transitive-closure/{ontology_term_id_end}'
    ]
  },
  pathways_pathways: { type: 'edge', endpoints: ['/pathways/pathways'] },
  proteins_proteins: { type: 'edge', endpoints: ['/proteins/proteins'] },
  transcripts_genes_structure: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  transcripts_proteins: { type: 'edge', endpoints: ['/transcripts/proteins', '/proteins/transcripts'] },
  variants_biosamples: { type: 'edge', endpoints: ['/variants/biosamples', '/biosamples/variants'] },
  variants_coding_variants: { type: 'edge', endpoints: ['/variants/coding-variants', '/coding-variants/variants'] },
  variants_diseases: { type: 'edge', endpoints: ['/variants/diseases', '/diseases/variants'] },
  variants_diseases_genes: { type: 'edge', endpoints: ['/genes/diseases', '/diseases/genes'] },
  variants_drugs: { type: 'edge', endpoints: ['/variants/drugs', '/drugs/variants'] },
  variants_drugs_genes: { type: 'edge', endpoints: [] }, // no dedicated endpoint exists yet
  variants_genes: {
    type: 'edge',
    endpoints: ['/variants/genes', '/genes/variants', '/variants/genes/summary', '/qtls', '/variants/genes-proteins']
  },
  variants_genomic_elements: {
    type: 'edge',
    endpoints: [
      '/variants/genomic-elements',
      '/genomic-elements/variants',
      '/variants/predictions',
      '/variants/predictions-count',
      '/variants/region-summary',
      '/variants/genomic-elements/cell-gene-predictions',
      '/qtls'
    ]
  },
  variants_phenotypes: { type: 'edge', endpoints: ['/variants/phenotypes', '/phenotypes/variants'] },
  variants_proteins: { type: 'edge', endpoints: ['/variants/proteins', '/proteins/variants', '/qtls', '/variants/genes-proteins'] },
  variants_variants: { type: 'edge', endpoints: ['/variants/variant-ld', '/variants/variant-ld/summary'] }
}

/**
 * Throws if COLLECTION_ENDPOINTS drifts from its two sources of truth:
 *  - data/schemas/registry.json: every node/edge collection that actually
 *    exists must have an entry here (even if endpoints: []).
 *  - catalogEndpoints.ts: every endpoint path used above must be a real,
 *    registered API path (catches typos and stale paths after a rename).
 * Same "fail loudly at startup, not silently at query time" approach as
 * openApiDocument's own completeness check in src/openapi.ts.
 */
export function validateCollectionEndpoints (): void {
  const registryPath = path.join(__dirname, '..', 'data/schemas/registry.json')
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'))
  const registryCollections = new Set<string>([...Object.keys(registry.nodes), ...Object.keys(registry.edges)])

  const missingFromTable = Array.from(registryCollections).filter((name) => !(name in COLLECTION_ENDPOINTS))
  if (missingFromTable.length > 0) {
    throw new Error(`COLLECTION_ENDPOINTS is missing registry collections: ${missingFromTable.join(', ')}`)
  }

  const extraInTable = Object.keys(COLLECTION_ENDPOINTS).filter((name) => !registryCollections.has(name))
  if (extraInTable.length > 0) {
    throw new Error(`COLLECTION_ENDPOINTS has entries not present in registry.json: ${extraInTable.join(', ')}`)
  }

  const validPaths = new Set(CATALOG_ENDPOINTS.map(({ path: endpointPath }) => endpointPath))
  for (const [collection, { endpoints }] of Object.entries(COLLECTION_ENDPOINTS)) {
    for (const endpoint of endpoints) {
      if (!validPaths.has(endpoint)) {
        throw new Error(`COLLECTION_ENDPOINTS['${collection}'] references unknown endpoint: ${endpoint}`)
      }
    }
  }
}

validateCollectionEndpoints()
