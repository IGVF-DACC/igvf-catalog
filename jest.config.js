module.exports = {
  roots: ['<rootDir>'],
  transform: {
    '^.+\\.ts?$': 'ts-jest'
  },
  testRegex: '(/__tests__/.*|(\\.|/)(test|spec))\\.ts?$',
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  collectCoverage: true,
  clearMocks: true,
  coverageDirectory: 'coverage',
  coverageProvider: 'v8',
  collectCoverageFrom: [
    'src/env.ts',
    'src/trpc.ts',
    'src/routers/datatypeRouters/nodes/*.ts'
  ],
  coverageReporters: ['lcov', 'text'],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/coverage/',
    '/cdk_swagger/cdk.out/',
    '\\.d\\.ts$',
    '\\.d\\.js$'
  ],
  modulePathIgnorePatterns: [
    '/dist/',
    '/cdk_swagger/cdk.out/'
  ]
}
