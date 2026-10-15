# Internal analytics panel

A local-only tool for answering "which endpoints are popular, how slow are they, and was that slowness actually the database being under load?" It is never deployed - it only runs on your own machine, reading data that already exists rather than recording anything new.

## What it does

- **Popular paths and response times.** Reads this app's own nginx access log (the container in front of the API logs every request to CloudWatch, including `request_time`) via CloudWatch Logs Insights, and shows, per endpoint: hit count, avg/min/max/p95 response time, and a breakdown of the specific repeated calls (query strings) behind that traffic. The log group is found by pattern search, not a hardcoded name, so it keeps working even if the underlying CloudWatch log group gets recreated.
- **Database health for the same window.** Reads ArangoDB's own slow-query log (`db.listSlowQueries()`) and its queue-time signal (`db.queueTime`, populated from the `x-arango-queue-time-seconds` response header). The queue-time number is what lets you tell "this one endpoint is slow" apart from "the whole database was backed up at that moment" - a DB-wide contention spike will show up here regardless of which endpoint you're looking at.

It does not write anything anywhere - no new database collection, no per-request instrumentation, no middleware in the main app. It only reads two things that already exist.

## Launching it

```bash
npm run analytics
```

This starts a small Express server bound to `127.0.0.1` only (not reachable from the network) and prints the URL to open, by default `http://127.0.0.1:4023/internal/analytics`. There is no login/token - being local-only is the access control.

## Configuring it

Two things need credentials, both already using patterns the rest of this repo uses:

- **AWS.** Needs a session with CloudWatch Logs read access (`logs:DescribeLogGroups`, `logs:StartQuery`, `logs:GetQueryResults`) in `us-west-2`, for whichever AWS account you want to inspect (the dev/demo account or the production account). Typically this just means having a valid SSO session and pointing at the right profile:
  ```bash
  AWS_PROFILE=igvf-dev npm run analytics
  ```
- **Database.** Uses the same ArangoDB connection as the main app (`src/database.ts`). With no extra setup it talks to the dev database from `config/development.json`. To point it at a different database, set the same override env vars the deployed app uses:
  ```bash
  ENV=production \
  IGVF_CATALOG_ARANGODB_URI=... \
  IGVF_CATALOG_ARANGODB_DBNAME=... \
  IGVF_CATALOG_ARANGODB_USERNAME=... \
  IGVF_CATALOG_ARANGODB_PASSWORD=... \
  npm run analytics
  ```

## Using the panel

- **Stage** picks which AWS account's nginx log group to query - `dev` or `production`. Each account can only ever see its own data, so picking the wrong one for the AWS session you're using just fails cleanly (no data, no cross-account leak) rather than returning the wrong environment's numbers.
- **Hours** sets the lookback window for both the CloudWatch query and how "recent" the slow-query list needs to be interpreted as.
- **Load** runs the query. CloudWatch Logs Insights queries are asynchronous and get polled, so this can take up to ~30 seconds - the status line says so while it's working.
- Long values (query text, bind vars, popular-call breakdowns, and the exact endpoint behind a min/max time) are collapsed behind a small `N repeated call(s)` / truncated-text summary - click it to expand into a selectable, copyable block instead of a browser tooltip.

## Known limitations

- Only `dev` and `production` are supported - `demo` (ephemeral per-PR preview deploys) isn't, since it's not a persistent environment worth tracking.
- The "popular calls" and min/max-example breakdown are derived from a bounded, globally-sorted sample of calls (see `MAX_CALLS_ROWS` in `src/internal/analytics.ts`), not the complete traffic in the window. A path whose traffic is entirely long-tail (each distinct call happening once) may show no breakdown even though the path itself has real traffic. The path-level hits/avg/min/max/p95 numbers themselves are always exact.
- CloudFront cache-hit data isn't available: a cache hit is served straight from the edge and never reaches the nginx origin, so it can't appear in this log by construction, and CloudFront's own `CacheHitRate` metric requires enabling a paid "additional metrics" subscription that isn't turned on.

## Where the code lives

- `src/internal/analytics.ts` - the CloudWatch/ArangoDB queries, the JSON endpoint, and the panel's HTML/JS.
- `src/internal/analyticsServer.ts` - the standalone local entry point (`npm run analytics` runs this).
