import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './server'
import { envData } from './env'

export const openApiDocument = generateOpenApiDocument(appRouter, {
  title: 'IGVF Catalog',
  description: 'IGVF Catalog OpenAPI compliant REST API built using tRPC with Express',
  version: '0.0.1',
  baseUrl: `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`,
  docsUrl: 'https://github.com/IGVF-DACC/igvf-catalog'
})
