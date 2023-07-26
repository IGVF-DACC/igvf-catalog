import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { envData } from './env'

let baseUrl = `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`
// prevents producation SSL cert mismatch
if (envData.host.port === 80) {
  baseUrl = `${envData.host.protocol}://${envData.host.hostname}/api`
}

export const openApiDocument = generateOpenApiDocument(appRouter, {
  title: 'IGVF Catalog',
  description: 'IGVF Catalog OpenAPI compliant REST API built using tRPC with Express',
  version: '0.0.1',
  docsUrl: 'https://github.com/IGVF-DACC/igvf-catalog',
  baseUrl
})
