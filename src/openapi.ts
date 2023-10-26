import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { envData } from './env'

let baseUrl = `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`
// prevents producation SSL cert mismatch
if (envData.host.port === 80) {
  baseUrl = `${envData.host.protocol}://${envData.host.hostname}/api`
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

export const openApiDocument = generateOpenApiDocument(appRouter, openApiConfig)
