# `parseRangeFilter` for log10pvalue

The original AQL code used `getFilterStatements()` to parse range expressions. The ClickHouse version has a standalone `parseRangeFilter()` that supports `gte:5`, `lt:10`, `range:5-10`, and bare numbers. It returns a structured object used by `pvalueCondition()` to build parameterized SQL conditions:

```typescript
// Input: "gte:5" → Output: vps.log10pvalue >= {_pval:Float64} with params { _pval: 5 }
// Input: "range:5-10" → Output: vps.log10pvalue >= {_pval_lo:Float64} AND ... < {_pval_hi:Float64}
```
