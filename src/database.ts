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
    connections: number
    pipelining: number
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
    connections: dbConfig.agentOptions.connections,
    pipelining: dbConfig.agentOptions.pipelining,
    timeout: dbConfig.agentOptions.timeout
  }
}

export const db = new Database(configuration)
