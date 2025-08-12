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
  collectCoverageFrom: [
    'src/env.ts',
    'src/trpc.ts',
    'src/routers/datatypeRouters/**/*.ts',
    '!src/routers/datatypeRouters/**/*.d.ts',
    '!src/routers/datatypeRouters/**/__tests__/**',
    '!src/routers/datatypeRouters/**/*.test.ts',
    '!src/routers/datatypeRouters/**/*.spec.ts'
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
