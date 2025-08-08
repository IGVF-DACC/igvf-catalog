/* eslint-disable @typescript-eslint/no-var-requires */
describe('System configuration', () => {
  const env = process.env

  const validConfiguration = {
    environment: 'development',
    host: {
      protocol: 'http',
      hostname: 'localhost',
      port: 2023
    },
    database: {
      connectionUri: 'https://db-dev.catalog.igvf.org/',
      dbName: 'igvf',
      auth: {
        username: 'igvf',
        password: 'igvf2023'
      }
    },
    catalog_llm_query_service_url: 'https://catalog-llm-dev.demo.igvf.org/query'
  }

  beforeEach(() => {
    jest.resetModules()
    process.env = { ...env }
  })

  afterEach(() => {
    jest.clearAllMocks()
    process.env = env
  })

  describe('loads valid configuration file', () => {
    test('loads development.json by default', () => {
      const mockConfig = validConfiguration
      jest.mock('../../config/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
    })

    test('loads custom config with same name as env', () => {
      process.env.ENV = 'myenv'

      const mockConfig = structuredClone(validConfiguration)
      mockConfig.environment = 'myenv'

      jest.mock('../../config/myenv.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
      expect(envData.environment).toBe('myenv')
    })

    test('loads ENV variables into config if in production mode', () => {
      process.env.ENV = 'production'
      process.env.IGVF_CATALOG_PROTOCOL = 'https'
      process.env.IGVF_CATALOG_HOSTNAME = 'test.igvf.org'
      process.env.IGVF_CATALOG_PORT = '8080'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'https://arangodb:8529/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'testdb'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'testuser'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'testpass'

      const mockConfig = structuredClone(validConfiguration)
      mockConfig.environment = 'production'

      jest.mock('../../config/production.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).toBe(process.env.IGVF_CATALOG_HOSTNAME)
      expect(envData.host.protocol).toBe('https')
      expect(envData.host.port).toBe(parseInt(process.env.IGVF_CATALOG_PORT))
      expect(envData.database.connectionUri).toBe(process.env.IGVF_CATALOG_ARANGODB_URI)
      expect(envData.database.dbName).toBe(process.env.IGVF_CATALOG_ARANGODB_DBNAME)
      expect(envData.database.auth.username).toBe(process.env.IGVF_CATALOG_ARANGODB_USERNAME)
      expect(envData.database.auth.password).toBe(process.env.IGVF_CATALOG_ARANGODB_PASSWORD)

      expect(envData.environment).toBe('production')
    })

    test('loads ENV variables into config and default to config file for missing values', () => {
      process.env.ENV = 'production'
      process.env.IGVF_CATALOG_PROTOCOL = 'https'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'https://arangodb:8529/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'testdb'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'testuser'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'testpass'

      const mockConfig = structuredClone(validConfiguration)
      mockConfig.environment = 'production'

      jest.mock('../../config/production.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).toBe(validConfiguration.host.hostname)
      expect(envData.host.protocol).toBe('https')
      expect(envData.host.port).toBe(validConfiguration.host.port)
      expect(envData.database.connectionUri).toBe(process.env.IGVF_CATALOG_ARANGODB_URI)
      expect(envData.database.dbName).toBe(process.env.IGVF_CATALOG_ARANGODB_DBNAME)
      expect(envData.database.auth.username).toBe(process.env.IGVF_CATALOG_ARANGODB_USERNAME)
      expect(envData.database.auth.password).toBe(process.env.IGVF_CATALOG_ARANGODB_PASSWORD)

      expect(envData.environment).toBe('production')
    })

    test('do not load ENV variables into config if not in production mode', () => {
      process.env.ENV = 'development'
      process.env.IGVF_CATALOG_PROTOCOL = 'https'
      process.env.IGVF_CATALOG_HOSTNAME = 'test.igvf.org'
      process.env.IGVF_CATALOG_PORT = '8080'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'https://arangodb:8529/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'testdb'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'testuser'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'testpass'

      const mockConfig = structuredClone(validConfiguration)
      mockConfig.environment = 'development'

      jest.mock('../../config/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).toBe(validConfiguration.host.hostname)
      expect(envData.host.protocol).toBe(validConfiguration.host.protocol)
      expect(envData.host.port).toBe(validConfiguration.host.port)
      expect(envData.database.connectionUri).toBe(validConfiguration.database.connectionUri)
      expect(envData.database.dbName).toBe(validConfiguration.database.dbName)
      expect(envData.database.auth.username).toBe(validConfiguration.database.auth.username)
      expect(envData.database.auth.password).toBe(validConfiguration.database.auth.password)

      expect(envData.environment).toBe('development')
    })
  })

  describe('loads invalid configuration file', () => {
    test('it should fail', () => {
      const mockExit = jest.spyOn(process, 'exit').mockImplementation((number) => {
        throw new Error(`process exited: ${number as number}`)
      })

      const mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

      jest.mock('../../config/development.json', () => ({
        invalidKey: 'invalidValue'
      }), { virtual: true })

      expect(() => { require('../env') }).toThrow()
      expect(mockExit).toHaveBeenCalledWith(1)
      expect(mockConsoleError).toHaveBeenCalled()

      mockExit.mockRestore()
    })
  })
})
