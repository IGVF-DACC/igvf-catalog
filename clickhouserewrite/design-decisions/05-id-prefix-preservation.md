# ID prefix preservation for API compatibility

In ArangoDB, `record._from` returns values like `variants/NC_000001.11:91420:T:C`. In ClickHouse, the FK column `variants_id` stores just `NC_000001.11:91420:T:C`. API consumers may depend on the collection prefix, so non-verbose mode prepends it:

```typescript
variant: `variants/${row.variants_id}`
study: `studies/${row.studies_id}`
```
