describe('env.ts', () => {
  const OLD_ENV = process.env

  beforeEach(() => {
    jest.resetModules()
    process.env = { ...OLD_ENV }
  })

  afterAll(() => {
    process.env = OLD_ENV
  })

  it('loads default config in non-production environment', () => {
    process.env.ENV = 'development'
    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { envData } = require('../env')
      expect(envData.environment).toBe('development')
      expect(envData.host).toHaveProperty('protocol')
      expect(envData.database).toHaveProperty('connectionUri')
    })
  })

  it('overrides config with production environment variables', () => {
    process.env.ENV = 'production'
    process.env.IGVF_CATALOG_PROTOCOL = 'https'
    process.env.IGVF_CATALOG_HOSTNAME = 'prod.example.com'
    process.env.IGVF_CATALOG_PORT = '8080'
    process.env.IGVF_CATALOG_ARANGODB_URI = 'arangodb://prod'
    process.env.IGVF_CATALOG_ARANGODB_DBNAME = 'prod_db'
    process.env.IGVF_CATALOG_ARANGODB_USERNAME = 'prod_user'
    process.env.IGVF_CATALOG_ARANGODB_PASSWORD = 'prod_pass'
    process.env.IGVF_CATALOG_ARANGODB_AGENT_MAX_SOCKETS = '20'
    process.env.IGVF_CATALOG_ARANGODB_AGENT_KEEP_ALIVE = 'false'
    process.env.IGVF_CATALOG_ARANGODB_AGENT_TIMEOUT = '120000'
    process.env.IGVF_CATALOG_LLM_QUERY_SERVICE_URL = 'https://llm.prod'

    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { envData } = require('../env')
      expect(envData.environment).toBe('production')
      expect(envData.host.protocol).toBe('https')
      expect(envData.host.hostname).toBe('prod.example.com')
      expect(envData.host.port).toBe(8080)
      expect(envData.database.connectionUri).toBe('arangodb://prod')
      expect(envData.database.dbName).toBe('prod_db')
      expect(envData.database.auth.username).toBe('prod_user')
      expect(envData.database.auth.password).toBe('prod_pass')
      expect(envData.database.agentOptions.maxSockets).toBe(20)
      expect(envData.database.agentOptions.keepAlive).toBe(false)
      expect(envData.database.agentOptions.timeout).toBe(120000)
      expect(envData.catalog_llm_query_service_url).toBe('https://llm.prod')
    })
  })

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
