import express from 'express'
import compression from 'compression'
import cors from 'cors'
import morgan from 'morgan'
import path from 'path'
import { createStream } from 'rotating-file-stream'
import { createExpressMiddleware } from '@trpc/server/adapters/express'
import { createOpenApiExpressMiddleware } from 'trpc-to-openapi'
import { appRouter } from './routers/_app'
import { createContext } from './trpc'
import swaggerUi from 'swagger-ui-express'
import { openApiDocument, swaggerConfig } from './openapi'
import { envData } from './env'

const app = express()

if (process.env.ENV === 'production') {
  const accessLogStream = createStream('access.log', {
    interval: '1d',
    path: '/var/log/igvf-catalog',
    compress: 'gzip'
  })

  app.use(morgan('combined', { stream: accessLogStream }))
} else {
  app.use(morgan('dev'))
}

app.use(compression())
app.use(cors())

app.use('/trpc', createExpressMiddleware({ router: appRouter, createContext }))

app.use('/api', (req, _res, next) => {
  for (const key of Object.keys(req.query)) {
    if (req.query[key] === '') {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete req.query[key]
    }
  }
  next()
})
// eslint-disable-next-line @typescript-eslint/no-misused-promises
app.use('/api', createOpenApiExpressMiddleware({ router: appRouter, createContext }))

app.use('/', swaggerUi.serve)
app.get('/', swaggerUi.setup(openApiDocument, swaggerConfig))

app.get('/openapi', (_req, res) => {
  res.json(openApiDocument)
})

app.get('/robots.txt', (_req, res) => {
  res.sendFile('robots.txt', { root: path.join(__dirname, '../static') })
})

const server = app.listen(envData.host.port, () => {
  console.log(`Server started on: ${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}`)
})

server.setTimeout(300000)
