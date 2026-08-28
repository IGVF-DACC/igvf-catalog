/**
 * Swagger section tags and endpoint order from catalog_endpoints.tsv.
 * Document-level tag order defines section order in Swagger UI.
 */
export const OPENAPI_TAG_ORDER = [
  'Nodes',
  'IGVF Data',
  'Bespoke Endpoints',
  'Biological Context Data',
  'Utility Endpoints'
] as const

export type OpenApiTag = (typeof OPENAPI_TAG_ORDER)[number]

/** Ordered list of API paths (with leading /) and their Swagger tags. */
export const CATALOG_ENDPOINTS: ReadonlyArray<{ path: string, tag: OpenApiTag }> = [
  // Nodes
  { path: '/variants', tag: 'Nodes' },
  { path: '/coding-variants', tag: 'Nodes' },
  { path: '/genomic-elements', tag: 'Nodes' },
  { path: '/genes', tag: 'Nodes' },
  { path: '/genes-structure', tag: 'Nodes' },
  { path: '/transcripts', tag: 'Nodes' },
  { path: '/proteins', tag: 'Nodes' },
  { path: '/complexes', tag: 'Nodes' },
  { path: '/pathways', tag: 'Nodes' },
  { path: '/motifs', tag: 'Nodes' },
  { path: '/drugs', tag: 'Nodes' },
  { path: '/ontology-terms', tag: 'Nodes' },
  { path: '/studies', tag: 'Nodes' },
  // IGVF Data
  { path: '/variants/genomic-elements', tag: 'IGVF Data' },
  { path: '/variants/genes', tag: 'IGVF Data' },
  { path: '/variants/proteins', tag: 'IGVF Data' },
  { path: '/variants/phenotypes', tag: 'IGVF Data' },
  { path: '/variants/biosamples', tag: 'IGVF Data' },
  { path: '/proteins/variants', tag: 'IGVF Data' },
  { path: '/proteins/proteins', tag: 'IGVF Data' },
  { path: '/phenotypes/variants', tag: 'IGVF Data' },
  { path: '/phenotypes/coding-variants', tag: 'IGVF Data' },
  { path: '/phenotypes/genomic-elements', tag: 'IGVF Data' },
  { path: '/genomic-elements/variants', tag: 'IGVF Data' },
  { path: '/genomic-elements/genes', tag: 'IGVF Data' },
  { path: '/genomic-elements/phenotypes', tag: 'IGVF Data' },
  { path: '/genomic-elements/biosamples', tag: 'IGVF Data' },
  { path: '/genes/variants', tag: 'IGVF Data' },
  { path: '/genes/genomic-elements', tag: 'IGVF Data' },
  { path: '/coding-variants/phenotypes', tag: 'IGVF Data' },
  { path: '/biosamples/variants', tag: 'IGVF Data' },
  { path: '/biosamples/genomic-elements', tag: 'IGVF Data' },
  // Bespoke Endpoints
  { path: '/variants/freq', tag: 'Bespoke Endpoints' },
  { path: '/gene-regulatory-network', tag: 'Bespoke Endpoints' },
  { path: '/enhancer-gene-predictions', tag: 'Bespoke Endpoints' },
  { path: '/qtls', tag: 'Bespoke Endpoints' },
  { path: '/variants/summary', tag: 'Bespoke Endpoints' },
  { path: '/variants/variant-ld/summary', tag: 'Bespoke Endpoints' },
  { path: '/variants/region-summary', tag: 'Bespoke Endpoints' },
  { path: '/variants/genes/summary', tag: 'Bespoke Endpoints' },
  { path: '/variants/predictions-count', tag: 'Bespoke Endpoints' },
  { path: '/variants/predictions', tag: 'Bespoke Endpoints' },
  { path: '/variants/phenotypes/score-summary', tag: 'Bespoke Endpoints' },
  { path: '/variants/nearest-genes', tag: 'Bespoke Endpoints' },
  { path: '/variants/gnomad-alleles', tag: 'Bespoke Endpoints' },
  { path: '/variants/genomic-elements/genes', tag: 'Bespoke Endpoints' },
  { path: '/variants/genomic-elements/cell-gene-predictions', tag: 'Bespoke Endpoints' },
  { path: '/variants/genes-proteins', tag: 'Bespoke Endpoints' },
  { path: '/genes/coding-variants/scores', tag: 'Bespoke Endpoints' },
  { path: '/genes/coding-variants/all-scores', tag: 'Bespoke Endpoints' },
  { path: '/genes-proteins/variants', tag: 'Bespoke Endpoints' },
  { path: '/genes-proteins/genes-proteins', tag: 'Bespoke Endpoints' },
  { path: '/coding-variants/phenotypes/score-summary', tag: 'Bespoke Endpoints' },
  { path: '/coding-variants/phenotypes-count', tag: 'Bespoke Endpoints' },
  { path: '/ontology-terms/{ontology_term_id}/parents', tag: 'Bespoke Endpoints' },
  { path: '/ontology-terms/{ontology_term_id}/children', tag: 'Bespoke Endpoints' },
  { path: '/ontology-terms/{ontology_term_id_start}/transitive-closure/{ontology_term_id_end}', tag: 'Bespoke Endpoints' },
  // Biological Context Data
  { path: '/variants/variant-ld', tag: 'Biological Context Data' },
  { path: '/variants/coding-variants', tag: 'Biological Context Data' },
  { path: '/variants/drugs', tag: 'Biological Context Data' },
  { path: '/variants/diseases', tag: 'Biological Context Data' },
  { path: '/coding-variants/variants', tag: 'Biological Context Data' },
  { path: '/genes/transcripts', tag: 'Biological Context Data' },
  { path: '/genes/proteins', tag: 'Biological Context Data' },
  { path: '/genes/pathways', tag: 'Biological Context Data' },
  { path: '/genes/genes', tag: 'Biological Context Data' },
  { path: '/genes/diseases', tag: 'Biological Context Data' },
  { path: '/transcripts/genes', tag: 'Biological Context Data' },
  { path: '/transcripts/proteins', tag: 'Biological Context Data' },
  { path: '/proteins/transcripts', tag: 'Biological Context Data' },
  { path: '/proteins/genes', tag: 'Biological Context Data' },
  { path: '/proteins/complexes', tag: 'Biological Context Data' },
  { path: '/complexes/proteins', tag: 'Biological Context Data' },
  { path: '/proteins/motifs', tag: 'Biological Context Data' },
  { path: '/motifs/proteins', tag: 'Biological Context Data' },
  { path: '/pathways/genes', tag: 'Biological Context Data' },
  { path: '/pathways/pathways', tag: 'Biological Context Data' },
  { path: '/go-terms/gene-products', tag: 'Biological Context Data' },
  { path: '/gene-products/go-terms', tag: 'Biological Context Data' },
  { path: '/diseases/variants', tag: 'Biological Context Data' },
  { path: '/diseases/genes', tag: 'Biological Context Data' },
  { path: '/drugs/variants', tag: 'Biological Context Data' },
  // Utility Endpoints
  { path: '/files-filesets', tag: 'Utility Endpoints' },
  { path: '/llm-query', tag: 'Utility Endpoints' },
  { path: '/autocomplete', tag: 'Utility Endpoints' },
  { path: '/health', tag: 'Utility Endpoints' }
]

export const PATH_TO_TAG: Readonly<Record<string, OpenApiTag>> = Object.fromEntries(
  CATALOG_ENDPOINTS.map(({ path, tag }) => [path, tag])
) as Record<string, OpenApiTag>
