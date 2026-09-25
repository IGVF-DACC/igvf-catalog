module.exports = {
  roots: ['<rootDir>'],
  transform: {
    '^.+\\.ts?$': 'ts-jest'
  },
  testRegex: '(/__tests__/integration/.*)\\.integration\\.test\\.ts$',
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],
  // Serial on purpose: these tests hit the real shared dev ArangoDB
  // (db-dev.catalog.igvf.org) - never run them concurrently.
  maxWorkers: 1,
  collectCoverage: false,
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/coverage/',
    '/cdk_swagger/cdk.out/'
  ],
  modulePathIgnorePatterns: [
    '/dist/',
    '/cdk_swagger/cdk.out/'
  ]
}
