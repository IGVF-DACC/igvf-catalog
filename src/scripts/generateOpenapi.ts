import fs from 'fs'
import path from 'path'
import { openApiDocument } from '../openapi'

const outFile = process.argv[2] ?? 'openapi.json'

fs.mkdirSync(path.dirname(outFile), { recursive: true })
fs.writeFileSync(outFile, JSON.stringify(openApiDocument, null, 2) + '\n')

console.log(`Wrote ${Object.keys(openApiDocument.paths).length} paths to ${outFile}`)
