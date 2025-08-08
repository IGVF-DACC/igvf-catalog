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
