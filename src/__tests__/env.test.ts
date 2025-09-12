/* eslint-disable @typescript-eslint/no-var-requires */
const OLD_ENV = process.env

describe('System configuration', () => {
  const validEnvConfiguration = {
    environment: 'jestTest',
    host: {
      protocol: 'http',
      hostname: 'test_localhost',
      port: 2023
    },
    database: {
      connectionUri: 'http://127.0.0.1:8529/',
      dbName: 'igvf',
      auth: {
        username: 'user',
        password: 'psswd'
      }
    },
    catalog_llm_query_service_url: 'http://127.0.0.1:5000/query?'
  }

  const validEnvAgentConfiguration = {
    environment: 'jestTest',
    host: {
      protocol: 'http',
      hostname: 'test_localhost',
      port: 2023
    },
    database: {
      connectionUri: 'http://127.0.0.1:8529/',
      dbName: 'igvf',
      auth: {
        username: 'user',
        password: 'psswd'
      },
      agentOptions: {
        maxSockets: 10,
        keepAlive: true,
        timeout: 60000
      }
    },
    catalog_llm_query_service_url: 'http://127.0.0.1:5000/query?'
  }

  beforeEach(() => {
    jest.resetModules()
    process.env = { ...OLD_ENV }
  })

  afterEach(() => {
    jest.clearAllMocks()
    process.env = OLD_ENV
  })

  describe('loads valid configuration file', () => {
    test('loads development.json by default', () => {
      const mockConfig = validEnvConfiguration
      jest.mock('../../config/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
    })

    test('loads custom config with same name as env', () => {
      process.env.ENV = 'myenv'

      const mockConfig = structuredClone(validEnvConfiguration)
      mockConfig.environment = 'myenv'

      jest.mock('../../config/myenv.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
      expect(envData.environment).toBe('myenv')
    })

    test('loads ENV variables into config if in production mode', () => {
      process.env.ENV = 'production'
      process.env.IGVF_CATALOG_PROTOCOL = 'http'
      process.env.IGVF_CATALOG_HOSTNAME = 'test hostname'
      process.env.IGVF_CATALOG_PORT = '1234'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'http://arangodb:8765/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'test dbname'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'test username'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'test password'

      const mockConfig = structuredClone(validEnvConfiguration)
      mockConfig.environment = 'production'

      jest.mock('../../config/production.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).toBe(process.env.IGVF_CATALOG_HOSTNAME)
      expect(envData.host.protocol).toBe('http')
      expect(envData.host.port).toBe(parseInt(process.env.IGVF_CATALOG_PORT))
      expect(envData.database.connectionUri).toBe(process.env.IGVF_CATALOG_ARANGODB_URI)
      expect(envData.database.dbName).toBe(process.env.IGVF_CATALOG_ARANGODB_DBNAME)
      expect(envData.database.auth.username).toBe(process.env.IGVF_CATALOG_ARANGODB_USERNAME)
      expect(envData.database.auth.password).toBe(process.env.IGVF_CATALOG_ARANGODB_PASSWORD)

      expect(envData.environment).toBe('production')
    })

    test('loads ENV variables into config and default to config file for missing values', () => {
      process.env.ENV = 'production'
      process.env.IGVF_CATALOG_PROTOCOL = 'http'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'http://prod.arangodb:8765/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'prod dbname'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'prod username'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'prod password'

      const mockConfig = structuredClone(validEnvConfiguration)
      mockConfig.environment = 'production'

      jest.mock('../../config/production.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).toBe(validEnvConfiguration.host.hostname)
      expect(envData.host.protocol).toBe('http')
      expect(envData.host.port).toBe(validEnvConfiguration.host.port)

      expect(envData.database.connectionUri).toBe(process.env.IGVF_CATALOG_ARANGODB_URI)
      expect(envData.database.dbName).toBe(process.env.IGVF_CATALOG_ARANGODB_DBNAME)
      expect(envData.database.auth.username).toBe(process.env.IGVF_CATALOG_ARANGODB_USERNAME)
      expect(envData.database.auth.password).toBe(process.env.IGVF_CATALOG_ARANGODB_PASSWORD)

      expect(envData.environment).toBe('production')
    })

    test('do not load ENV variables into config if not in production mode', () => {
      process.env.ENV = 'development'
      process.env.IGVF_CATALOG_PROTOCOL = 'http'
      process.env.IGVF_CATALOG_HOSTNAME = 'prod test hostname'
      process.env.IGVF_CATALOG_PORT = '1234'
      process.env.IGVF_CATALOG_ARANGODB_URI = 'http://prod.arangodb:8765/'
      process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'prod dbname'
      process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'prod username'
      process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'prod password'

      const mockConfig = structuredClone(validEnvAgentConfiguration)
      mockConfig.environment = 'development'
      jest.mock('../../config/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData.host.hostname).not.toBe(process.env.IGVF_CATALOG_HOSTNAME)
      expect(envData.host.port).not.toBe(parseInt(process.env.IGVF_CATALOG_PORT))
      expect(envData.database.connectionUri).not.toBe(process.env.IGVF_CATALOG_ARANGODB_URI)
      expect(envData.database.dbName).not.toBe(process.env.IGVF_CATALOG_ARANGODB_DBNAME)
      expect(envData.database.auth.username).not.toBe(process.env.IGVF_CATALOG_ARANGODB_USERNAME)
      expect(envData.database.auth.password).not.toBe(process.env.IGVF_CATALOG_ARANGODB_PASSWORD)

      expect(envData.environment).toBe('development')
    })

    test('loads agentOptions optional data', () => {
      const mockConfig = validEnvAgentConfiguration
      jest.mock('../../config/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
    })
  })

  describe('loads invalid configuration file', () => {
    test('it should fail', () => {
      const mockExit = jest.spyOn(process, 'exit').mockImplementation((number) => {
        // eslint-disable-next-line @typescript-eslint/restrict-plus-operands
        throw new Error('process exitted: ' + number)
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
