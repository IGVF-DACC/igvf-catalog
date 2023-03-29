import express from 'express'
import compression from 'compression'
import { createExpressMiddleware } from '@trpc/server/adapters/express'
import { createOpenApiExpressMiddleware } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { createContext } from './trpc'
import swaggerUi from 'swagger-ui-express'
import { openApiDocument } from './openapi'
import { envData } from './env'

const app = express()

app.use(compression())

app.use('/trpc', createExpressMiddleware({ router: appRouter, createContext }))
// eslint-disable-next-line @typescript-eslint/no-misused-promises
app.use('/api', createOpenApiExpressMiddleware({ router: appRouter, createContext }))

app.use('/', swaggerUi.serve)
app.get('/', swaggerUi.setup(openApiDocument))

app.listen(envData.host.port, () => {
  console.log(`Server started on: ${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}`)
})
