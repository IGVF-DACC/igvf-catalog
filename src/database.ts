import { Database } from 'arangojs'
import { envData } from './env'

const dbConfig = envData.database

interface Configuration {
  url: string
  databaseName: string
  auth: {
    username: string
    password: string
  }
  agentOptions?: {
    maxSockets: number
    keepAlive: boolean
    timeout: number
  }
}

const configuration: Configuration = {
  url: dbConfig.connectionUri,
  databaseName: dbConfig.dbName,
  auth: {
    username: dbConfig.auth.username,
    password: dbConfig.auth.password
  }
}

if (dbConfig.agentOptions !== undefined) {
  configuration.agentOptions = {
    maxSockets: dbConfig.agentOptions.maxSockets,
    keepAlive: dbConfig.agentOptions.keepAlive,
    timeout: dbConfig.agentOptions.timeout
  }
}

export const db = new Database(configuration)
