/* eslint-disable @typescript-eslint/no-var-requires */
describe('System configuration', () => {
  const env = process.env

  beforeEach(() => {
    jest.resetModules()
    process.env = { ...env }
  })

  afterEach(() => {
    jest.clearAllMocks()
    process.env = env
  })

  describe('loads valid configuration file', () => {
    const validConfiguration = {
      environment: 'jestTest',
      host: {
        protocol: 'http',
        hostname: 'localhost',
        port: 2023
      },
      database: {
        connectionUri: 'http://127.0.0.1:8529/',
        dbName: 'igvf',
        auth: {
          username: 'user',
          password: 'psswd'
        }
      }
    }

    test('loads development.json by default', () => {
      const mockConfig = validConfiguration
      jest.mock('../env/development.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
    })

    test('loads custom config with same name as env', () => {
      process.env.ENV = 'myenv'

      const mockConfig = structuredClone(validConfiguration)
      mockConfig.environment = 'myenv'

      jest.mock('../env/myenv.json', () => { return mockConfig }, { virtual: true })

      const { envData } = require('../env')
      expect(envData).toEqual(mockConfig)
      expect(envData.environment).toBe('myenv')
    })
  })

  describe('loads invalid configuration file', () => {
    test('it should fail', () => {
      const mockExit = jest.spyOn(process, 'exit').mockImplementation((number) => {
        // eslint-disable-next-line @typescript-eslint/restrict-plus-operands
        throw new Error('process exitted: ' + number)
      })

      const mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

      jest.mock('../env/development.json', () => ({
        invalidKey: 'invalidValue'
      }), { virtual: true })

      expect(() => { require('../env') }).toThrow()
      expect(mockExit).toHaveBeenCalledWith(1)
      expect(mockConsoleError).toHaveBeenCalled()

      mockExit.mockRestore()
    })
  })
})
