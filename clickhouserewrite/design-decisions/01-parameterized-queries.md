# Parameterized queries for SQL injection prevention

The `variants.ts` prototype used an `esc()` helper with string interpolation to build SQL. For `variants_phenotypes.ts`, we switched to ClickHouse's native parameterized queries using the `{name:Type}` syntax with `query_params`:

```typescript
async function chQuery<T = any>(sql: string, params?: QueryParams): Promise<T[]> {
  const resultSet = await db.query({
    query: sql,
    query_params: params,
    format: 'JSONEachRow'
  })
  return await resultSet.json()
}
```

All user-supplied values (phenotype IDs, method, class, label, fileset names) go through `query_params` and are never interpolated into the SQL string. This eliminates SQL injection by design.

The one exception is the `sqlInList()` helper used for arrays of internal IDs (from `variantIDSearch()` or the VP page query). These IDs originate from our own database queries, not from user input, and are single-quote escaped as a safety measure.
