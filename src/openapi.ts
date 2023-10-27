import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { envData } from './env'

let baseUrl = `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`
// prevents producation SSL cert mismatch
if (envData.host.port === 80) {
  baseUrl = `${envData.host.protocol}://${envData.host.hostname}/api`
}

export const swaggerConfig = {
  swaggerOptions: {
    tryItOutEnabled: true
  }
}

let openApiConfig = {
  title: 'IGVF Catalog - Development',
  description: 'Development IGVF Catalog OpenAPI compliant REST API built using tRPC with Express',
  version: '0.1.0 - DEV',
  docsUrl: 'https://api-dev.catalog.igvf.org/openapi',
  baseUrl
}

if (process.env.ENV === 'production') {
  openApiConfig = {
    title: 'IGVF Catalog',
    description: 'IGVF Catalog OpenAPI compliant REST API built using tRPC with Express',
    version: '0.1.0',
    docsUrl: 'https://api.catalog.igvf.org/openapi',
    baseUrl
  }
}

// Order defined by endpoints that have the following prefixes
const endpointsOrder = [
  '/variants',
  '/genes',
  '/transcripts',
  '/proteins',
  '/regulatory_regions',
  '/diseases',
  '/phenotypes',
  '/ontology_terms',
  '/go',
  '/motifs',
  '/studies',
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
