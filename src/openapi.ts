import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { envData } from './env'

let baseUrl = `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`
// prevents production SSL cert mismatch and use default ports
if (envData.host.port === 80 || envData.host.port === 443 || envData.environment === 'production') {
  baseUrl = `${envData.host.protocol}://${envData.host.hostname}/api`
}

export const swaggerConfig = {
  customCss: '.swagger-ui .opblock-description-wrapper p {font-size: 18px; line-height: 1.5em}',
  swaggerOptions: {
    tryItOutEnabled: true
  }
}

const LICENSE = '\n\nData is licensed under the <a href=https://creativecommons.org/licenses/by/4.0/ target="_blank">Creative Commons license</a> and the software is licensed under the <a href=https://spdx.org/licenses/MIT.html target="_blank">MIT license</a>.'
const GENOMIC_COORDINATES = '\n\nOur database uses 0-based, half-open coordinates for genomic coordinates in the GRCh38 (human) and GRCm39 (mouse) reference genomes.'

let openApiConfig = {
  title: 'IGVF Catalog - Development',
  description: 'Development IGVF Catalog OpenAPI compliant REST API built using tRPC with Express.' + GENOMIC_COORDINATES + LICENSE,
  version: '1.0.0 - DEV',
  docsUrl: 'https://api-dev.catalog.igvf.org/openapi',
  baseUrl
}

if (process.env.IGVF_CATALOG_OPEN_API_CONFIG_TYPE === 'production') {
  openApiConfig = {
    title: 'IGVF Catalog',
    description: 'IGVF Catalog OpenAPI compliant REST API built using tRPC with Express.' + LICENSE,
    version: '1.0.0',
    docsUrl: 'https://api.catalog.igvf.org/openapi',
    baseUrl
  }
}

// Order defined by endpoints that have the following prefixes
const endpointsOrder = [
  '/variants',
  '/coding-variants',
  '/genes',
  '/gene-products',
  '/transcripts',
  '/proteins',
  '/genomic-elements',
  '/diseases',
  '/phenotypes',
  '/ontology-terms',
  '/go',
  '/motifs',
  '/studies',
  '/complex',
  '/drugs',
  '/'
]

export const openApiDocument = generateOpenApiDocument(appRouter, openApiConfig)

const endpoints = Object.keys(openApiDocument.paths).sort((a, b) => { return a.length - b.length })
const endpointsCheck = endpoints.map((endpoint) => [endpoint, false])

const orderedList: string[] = []

endpointsOrder.forEach(prefix => {
  endpointsCheck.forEach(endpointMap => {
    if (endpointMap[1] === false && (endpointMap[0] as string).startsWith(prefix)) {
      orderedList.push(endpointMap[0] as string)

      endpointMap[1] = true
    }
  })
})

const newPath: typeof openApiDocument.paths = {}
orderedList.forEach((endpoint) => {
  newPath[endpoint] = openApiDocument.paths[endpoint]
})

openApiDocument.paths = newPath
