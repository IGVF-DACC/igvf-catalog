import express from 'express'
import { internalAnalyticsRouter } from './analytics'

// Run with `npm run analytics`. This is deliberately never deployed - see
// src/internal/analytics.ts for why. Binds to localhost only.
const PORT = 4023
const HOSTNAME = '127.0.0.1'

const app = express()
app.use('/internal/analytics', internalAnalyticsRouter)

app.listen(PORT, HOSTNAME, () => {
  console.log(`Analytics panel: http://${HOSTNAME}:${PORT}/internal/analytics`)
  console.log('Needs: an AWS session (e.g. AWS_PROFILE=igvf-dev) with CloudWatch Logs read access, and ArangoDB credentials (defaults to config/development.json; override with IGVF_CATALOG_ARANGODB_* + ENV=production for a different DB).')
})
