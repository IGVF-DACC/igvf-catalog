import { Router, type Request, type Response } from 'express'
import { CloudWatchLogsClient, DescribeLogGroupsCommand, GetQueryResultsCommand, StartQueryCommand } from '@aws-sdk/client-cloudwatch-logs'
import { CloudFormationClient, DescribeStacksCommand, type Stack } from '@aws-sdk/client-cloudformation'
import { isArangoError, isNetworkError } from 'arangojs/errors'
import { db } from '../database'

// This is a LOCAL-ONLY tool (see src/internal/analyticsServer.ts) - it is
// never deployed, so there's no task role to grant IAM permissions to and
// no reason to gate it behind a token: it binds to localhost only, and
// whoever runs it uses their own AWS SSO session (needs read/query access
// to CloudWatch Logs for the account it's pointed at) and DB credentials
// (via IGVF_CATALOG_ARANGODB_* env vars, or the config/development.json
// defaults for zero setup against the dev DB).

// This whole file exists because the panel used to just say "Request failed: 500" on any
// failure, which was useless for anyone other than whoever had the server's stdout open -
// the exact complaint that prompted adding this (a coworker saw a blank panel with no way to
// tell whether her AWS session, her DB credentials, or something else entirely was the
// problem). classifyError() turns common AWS-credential and ArangoDB-connection failures
// into a plain-English summary that's sent straight to the browser; `detail` (the raw
// error.message) rides along for anything the summary doesn't fully capture.
interface ClassifiedError {
  summary: string
  detail: string
}

// Walks an Error's `cause` chain (Node/undici errors nest the real failure under `.cause`,
// sometimes more than one level deep - see e.g. FetchFailedError's cause -> TypeError ->
// cause -> the actual SystemError/UndiciError with `.code`) looking for a `.code` that
// identifies a low-level network failure.
function findCauseCode (error: unknown, maxDepth = 5): string | undefined {
  let current: any = error
  for (let i = 0; i < maxDepth && current != null; i++) {
    if (typeof current.code === 'string') {
      return current.code
    }
    current = current.cause
  }
  return undefined
}

// Names AWS's own error protocol uses for credential/auth problems - stable across SDK
// versions and services, since they come from the STS/IAM layer, not from
// @aws-sdk/client-cloudwatch-logs's generated exception classes.
const AWS_MISSING_CREDENTIALS_NAMES = new Set(['CredentialsProviderError', 'CredentialsNotFoundError'])
const AWS_INVALID_CREDENTIALS_NAMES = new Set([
  'ExpiredToken', 'ExpiredTokenException', 'UnrecognizedClientException',
  'InvalidClientTokenId', 'InvalidSignatureException', 'TokenRefreshRequired'
])
const AWS_ACCESS_DENIED_NAMES = new Set(['AccessDenied', 'AccessDeniedException', 'UnauthorizedException'])

function classifyError (error: unknown): ClassifiedError {
  const err = error as any
  const name: string | undefined = err?.name
  const message: string = err?.message ?? String(error)
  const detail = message

  // --- AWS / CloudWatch Logs ---
  if ((name !== undefined && AWS_MISSING_CREDENTIALS_NAMES.has(name)) || message.includes('Could not load credentials')) {
    return {
      summary: 'AWS credentials not found. Run `aws sso login` (or set AWS_PROFILE to a ' +
        'profile with access) before starting `npm run analytics`, then restart it - the AWS ' +
        'SDK only resolves credentials once, at process startup.',
      detail
    }
  }
  if (name !== undefined && AWS_INVALID_CREDENTIALS_NAMES.has(name)) {
    return {
      summary: 'AWS credentials were found but are invalid or expired. Run `aws sso login` ' +
        'and restart `npm run analytics`.',
      detail
    }
  }
  if (name !== undefined && AWS_ACCESS_DENIED_NAMES.has(name)) {
    return {
      summary: 'AWS credentials are valid but do not have permission to query CloudWatch ' +
        'Logs Insights for this account. Confirm you are logged into the account/role for ' +
        'the selected stage (dev vs production are different AWS accounts).',
      detail
    }
  }
  if (message.startsWith('No CloudWatch log group matched pattern')) {
    return {
      summary: 'Could not find the nginx access-log group for this stage - either the ' +
        'naming pattern in src/internal/analytics.ts is out of date, or your AWS session is ' +
        'pointed at the wrong account for this stage.',
      detail
    }
  }
  if (err?.$metadata !== undefined) {
    // A real AWS service responded (so credentials/network to AWS are fine) but with some
    // other error this function doesn't special-case - still worth labeling as AWS-side
    // rather than falling through to the generic case below.
    return { summary: `AWS CloudWatch Logs request failed: ${message}`, detail }
  }

  // --- ArangoDB ---
  if (isArangoError(error)) {
    if (error.code === 401 || error.errorNum === 401) {
      return {
        summary: 'ArangoDB rejected the credentials (401 Unauthorized). Check the username/' +
          'password in config/development.json, or your IGVF_CATALOG_ARANGODB_* env vars if ' +
          'you set ENV=production to point at a different DB.',
        detail
      }
    }
    return { summary: `ArangoDB query failed: ${message}`, detail }
  }
  const causeCode = findCauseCode(error)
  if (causeCode === 'ECONNREFUSED') {
    return {
      summary: 'Could not connect to ArangoDB - connection refused. Check the connectionUri ' +
        'in config/development.json (or IGVF_CATALOG_ARANGODB_* env vars) and confirm the DB ' +
        'host is actually reachable from this machine (VPN connected, etc.).',
      detail
    }
  }
  if (causeCode === 'ENOTFOUND' || causeCode === 'EAI_AGAIN') {
    return {
      summary: 'Could not resolve the ArangoDB hostname (DNS lookup failed). Double check ' +
        'the connectionUri in config/development.json / IGVF_CATALOG_ARANGODB_*.',
      detail
    }
  }
  if (causeCode === 'ETIMEDOUT' || causeCode === 'UND_ERR_CONNECT_TIMEOUT' || name === 'ResponseTimeoutError') {
    return {
      summary: 'Connection to ArangoDB timed out. Check VPN/network access to the DB host - ' +
        'this usually means the host is unreachable rather than just slow.',
      detail
    }
  }
  if (isNetworkError(error)) {
    return {
      summary: `Could not reach ArangoDB: ${message}. Check the connectionUri in ` +
        'config/development.json and your network/VPN connection to it.',
      detail
    }
  }

  return { summary: `Unexpected error: ${message}`, detail: err?.stack ?? message }
}

const POLL_INTERVAL_MS = 1000
const MAX_POLL_ATTEMPTS = 30
const DEFAULT_HOURS = 24
// Every account/region this app deploys to (dev, demo, production - see
// cdk_swagger/infrastructure/constructs/existing/{catalog_dev,catalog_prod}.py)
// is us-west-2; unlikely to change, so this is hardcoded rather than read
// from an AWS_REGION env var.
const AWS_REGION = 'us-west-2'

type Stage = 'dev' | 'production'

// This app's own nginx access-log group, found purely by pattern search.
// These substrings come from naming in cdk_swagger/infrastructure/naming.py
// and stages/{dev,production}.py: 'igvf-catalog-api-<branch>-<Stage>Deploy
// Stage-FrontendStack-...nginxLogGroup...', where <branch> is 'dev' for the
// dev pipeline and 'main' for the production pipeline (the branch that
// triggers each self-updating CodePipeline). The trailing ID is CDK/
// CloudFormation-autogenerated and can change across deploys, which is why
// this resolves it live via DescribeLogGroups rather than a fixed full name.
const LOG_GROUP_NAME_PATTERNS: Record<Stage, string> = {
  dev: 'igvf-catalog-api-dev-DevelopmentDeployStage-FrontendStack-FrontendFargateTaskDefnginxLogGroup',
  production: 'igvf-catalog-api-main-ProductionDeployStage-FrontendStack-FrontendFargateTaskDefnginxLogGroup'
}

// Picked in the panel UI, since a local AWS session may only have access to
// one of the two accounts (or both) - picking the wrong one just fails
// cleanly (no access to that account's log group) rather than returning
// another account's data.
function resolveStage (req: Request): Stage {
  return req.query.stage === 'production' ? 'production' : 'dev'
}

const cloudWatchLogsClient = new CloudWatchLogsClient({ region: AWS_REGION })
const cloudFormationClient = new CloudFormationClient({ region: AWS_REGION })

// Keyed by stage, since a single running process can be asked to resolve
// either stage (the panel lets a human pick per request) - caching one
// shared value here would leak whichever stage was resolved first into
// every later request regardless of what it actually asked for.
const nginxLogGroupNameCache = new Map<Stage, string>()

async function resolveNginxLogGroupName (stage: Stage): Promise<string> {
  const cached = nginxLogGroupNameCache.get(stage)
  if (cached !== undefined) {
    return cached
  }

  const pattern = LOG_GROUP_NAME_PATTERNS[stage]
  const candidates: Array<{ name: string, creationTime: number }> = []
  let nextToken: string | undefined

  do {
    const response = await cloudWatchLogsClient.send(new DescribeLogGroupsCommand({
      logGroupNamePattern: pattern,
      nextToken
    }))
    for (const group of response.logGroups ?? []) {
      if (group.logGroupName !== undefined) {
        candidates.push({ name: group.logGroupName, creationTime: group.creationTime ?? 0 })
      }
    }
    nextToken = response.nextToken
  } while (nextToken !== undefined)

  if (candidates.length === 0) {
    throw new Error(`No CloudWatch log group matched pattern "${pattern}"`)
  }

  // If a past deploy replaced the (CDK-autogenerated) log group, there may
  // be a stale leftover alongside the current one - the most recently
  // created match is the active one.
  candidates.sort((a, b) => b.creationTime - a.creationTime)
  const resolvedName = candidates[0].name
  nginxLogGroupNameCache.set(stage, resolvedName)
  return resolvedName
}

// Strips the query string (nginx logs it in full, so it isn't safe to group by)
// and pulls out the field nginx's custom log_format adds (docker/nginx/production.conf).
const TOP_PATHS_QUERY = `
parse @message /"(?<verb>\\S+) (?<urlpath>[^\\s?"]+)\\S* HTTP/
| parse @message /request_time=(?<request_time>[\\d.]+)/
| stats count(*) as hits, avg(request_time) as avg_s, min(request_time) as min_s, max(request_time) as max_s, pct(request_time, 95) as p95_s by urlpath
| sort hits desc
| limit 50
`

// Same idea, but keeps the query string too, to see which specific calls
// (not just which endpoint) are actually popular, and which one hit each
// path's min/max response time. Grouped globally rather than per-path,
// since Logs Insights has no "top N per group" - MAX_CALLS_ROWS is enough
// to cover the popular paths' popular calls, but a path whose traffic is
// mostly long-tail (each distinct call happening once) may come up short:
// its min/max example and popular-calls breakdown could point at whichever
// calls happened to make the cut, not the true extremes across every call
// ever made to it in the window (min_s/max_s on TOP_PATHS_QUERY above are
// still exact, since those aggregate over the complete, ungrouped dataset).
const MAX_CALLS_ROWS = 5000
const TOP_CALLS_PER_PATH = 8
const TOP_CALLS_QUERY = `
parse @message /"(?<verb>\\S+) (?<urlpath>[^\\s?"]+)(\\?(?<querystring>[^\\s"]*))? HTTP/
| parse @message /request_time=(?<request_time>[\\d.]+)/
| stats count(*) as hits, avg(request_time) as avg_s, min(request_time) as min_s, max(request_time) as max_s by urlpath, querystring
| sort hits desc
| limit ${MAX_CALLS_ROWS}
`

interface TopCall {
  querystring: string
  hits: number
  avgSeconds: number
}

interface TopPath {
  urlpath: string
  hits: number
  avgSeconds: number
  minSeconds: number
  maxSeconds: number
  p95Seconds: number
  minExampleQuerystring: string | undefined
  maxExampleQuerystring: string | undefined
  topCalls: TopCall[]
}

type SlowQuery = Awaited<ReturnType<typeof db.listSlowQueries>>[number]

interface DbHealthSnapshot {
  slowQueries: SlowQuery[]
  queueTimeAvg: number
  queueTimeLatest: number | undefined
}

async function sleep (ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms))
}

async function runInsightsQuery (logGroupName: string, startTime: number, endTime: number, queryString: string): Promise<Array<Record<string, string>>> {
  const startResponse = await cloudWatchLogsClient.send(new StartQueryCommand({
    logGroupName,
    startTime,
    endTime,
    queryString
  }))

  if (startResponse.queryId === undefined) {
    throw new Error('CloudWatch Logs Insights did not return a queryId')
  }

  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
    const results = await cloudWatchLogsClient.send(new GetQueryResultsCommand({ queryId: startResponse.queryId }))

    if (results.status === 'Complete') {
      return (results.results ?? []).map((row) => {
        const fields: Record<string, string> = {}
        for (const field of row) {
          if (field.field !== undefined && field.value !== undefined) {
            fields[field.field] = field.value
          }
        }
        return fields
      })
    }

    if (results.status === 'Failed' || results.status === 'Cancelled' || results.status === 'Timeout') {
      throw new Error(`CloudWatch Logs Insights query ended with status ${String(results.status)}`)
    }

    await sleep(POLL_INTERVAL_MS)
  }

  throw new Error('CloudWatch Logs Insights query timed out waiting for results')
}

function decodeQuerystring (querystring: string): string {
  try {
    return decodeURIComponent(querystring)
  } catch {
    return querystring
  }
}

interface PathExtremes {
  minSeconds: number
  minQuerystring: string
  maxSeconds: number
  maxQuerystring: string
}

async function queryCallBreakdownByPath (logGroupName: string, startTime: number, endTime: number): Promise<{
  topCallsByPath: Map<string, TopCall[]>
  extremesByPath: Map<string, PathExtremes>
}> {
  const rows = await runInsightsQuery(logGroupName, startTime, endTime, TOP_CALLS_QUERY)

  const topCallsByPath = new Map<string, TopCall[]>()
  const extremesByPath = new Map<string, PathExtremes>()

  for (const fields of rows) {
    if (fields.querystring === undefined) {
      continue
    }
    const urlpath = fields.urlpath ?? '(unmatched)'
    const querystring = decodeQuerystring(fields.querystring)
    const hits = Number(fields.hits ?? '0')
    const avgSeconds = Number(fields.avg_s ?? '0')
    const minSeconds = Number(fields.min_s ?? '0')
    const maxSeconds = Number(fields.max_s ?? '0')

    const topCalls = topCallsByPath.get(urlpath) ?? []
    if (topCalls.length < TOP_CALLS_PER_PATH) {
      topCalls.push({ querystring, hits, avgSeconds })
      topCallsByPath.set(urlpath, topCalls)
    }

    const extremes = extremesByPath.get(urlpath)
    if (extremes === undefined) {
      extremesByPath.set(urlpath, { minSeconds, minQuerystring: querystring, maxSeconds, maxQuerystring: querystring })
    } else {
      if (minSeconds < extremes.minSeconds) {
        extremes.minSeconds = minSeconds
        extremes.minQuerystring = querystring
      }
      if (maxSeconds > extremes.maxSeconds) {
        extremes.maxSeconds = maxSeconds
        extremes.maxQuerystring = querystring
      }
    }
  }

  return { topCallsByPath, extremesByPath }
}

async function queryTopPaths (logGroupName: string, startTime: number, endTime: number): Promise<TopPath[]> {
  const [pathRows, { topCallsByPath, extremesByPath }] = await Promise.all([
    runInsightsQuery(logGroupName, startTime, endTime, TOP_PATHS_QUERY),
    queryCallBreakdownByPath(logGroupName, startTime, endTime)
  ])

  return pathRows.map((fields) => {
    const urlpath = fields.urlpath ?? '(unmatched)'
    const extremes = extremesByPath.get(urlpath)
    return {
      urlpath,
      hits: Number(fields.hits ?? '0'),
      avgSeconds: Number(fields.avg_s ?? '0'),
      minSeconds: Number(fields.min_s ?? '0'),
      maxSeconds: Number(fields.max_s ?? '0'),
      p95Seconds: Number(fields.p95_s ?? '0'),
      minExampleQuerystring: extremes?.minQuerystring,
      maxExampleQuerystring: extremes?.maxQuerystring,
      topCalls: topCallsByPath.get(urlpath) ?? []
    }
  })
}

async function getDbHealthSnapshot (): Promise<DbHealthSnapshot> {
  const slowQueries = await db.listSlowQueries()
  slowQueries.sort((a, b) => b.runTime - a.runTime)
  return {
    slowQueries,
    queueTimeAvg: db.queueTime.getAvg(),
    queueTimeLatest: db.queueTime.getLatest()
  }
}

// Each demo branch deploys its own self-mutating CodePipeline stack
// (cdk_swagger/infrastructure/build.py's `add_deploy_pipeline_stack_to_app`
// names it '<project>-<branch>-DemoDeploymentPipelineStack'), which in turn
// deploys a '...-DemoDeployStage-FrontendStack' holding the actual Fargate
// service. That FrontendStack is tagged with project/branch/environment
// (infrastructure/tags.py) plus the cleanup tags demo stacks get in
// infrastructure/config.py ('time-to-live-hours', 'turn-off-on-friday-night')
// - this only reads those tags/outputs rather than computing "is it actually
// up" from ECS task counts, since the stack's own status already distinguishes
// a stable deploy from one that's mid-deploy or has failed.
const DEMO_PROJECT_TAG = 'igvf-catalog-api'
const DEMO_FRONTEND_STACK_SUFFIX = '-DemoDeployStage-FrontendStack'

interface DemoDeployment {
  branch: string
  url: string | undefined
  status: string
  createdAt: string | undefined
  updatedAt: string | undefined
  ttlHours: number | undefined
  turnOffOnFridayNight: boolean
  ageHours: number | undefined
  pastTtl: boolean
}

function tagValue (stack: Stack, key: string): string | undefined {
  return stack.Tags?.find((tag) => tag.Key === key)?.Value
}

function stackToDemoDeployment (stack: Stack): DemoDeployment {
  const branch = tagValue(stack, 'branch') ?? stack.StackName ?? '(unknown)'
  const url = stack.Outputs?.find((output) => output.OutputKey === 'FrontendUrl')?.OutputValue
  const ttlRaw = tagValue(stack, 'time-to-live-hours')
  const ttlHours = ttlRaw !== undefined ? Number(ttlRaw) : undefined
  const createdAt = stack.CreationTime?.toISOString()
  const ageHours = stack.CreationTime !== undefined
    ? (Date.now() - stack.CreationTime.getTime()) / (1000 * 60 * 60)
    : undefined

  return {
    branch,
    url,
    status: stack.StackStatus ?? '(unknown)',
    createdAt,
    updatedAt: stack.LastUpdatedTime?.toISOString(),
    ttlHours,
    turnOffOnFridayNight: tagValue(stack, 'turn-off-on-friday-night') === 'yes',
    ageHours,
    pastTtl: ttlHours !== undefined && ageHours !== undefined && ageHours > ttlHours
  }
}

async function queryDemoDeployments (): Promise<DemoDeployment[]> {
  const stacks: Stack[] = []
  let nextToken: string | undefined

  // DescribeStacks with no StackName returns every non-deleted stack in the
  // account in one paginated set (and, unlike ListStacks, includes Tags and
  // Outputs directly) - there's no server-side tag filter, so project/stack-
  // name matching happens client-side below.
  do {
    const response = await cloudFormationClient.send(new DescribeStacksCommand({ NextToken: nextToken }))
    stacks.push(...(response.Stacks ?? []))
    nextToken = response.NextToken
  } while (nextToken !== undefined)

  return stacks
    .filter((stack) =>
      stack.StackName?.endsWith(DEMO_FRONTEND_STACK_SUFFIX) === true &&
      tagValue(stack, 'project') === DEMO_PROJECT_TAG)
    .map(stackToDemoDeployment)
    .sort((a, b) => a.branch.localeCompare(b.branch))
}

function parseHours (rawHours: unknown): number {
  const hours = Number(rawHours)
  return Number.isFinite(hours) && hours > 0 ? hours : DEFAULT_HOURS
}

interface Section<T> {
  data: T | null
  error: ClassifiedError | null
}

// The AWS (CloudWatch) and ArangoDB sides are independent data sources with independent
// failure modes (an expired AWS SSO session has nothing to do with whether ArangoDB is
// reachable, and vice versa) - resolving each into its own Section rather than letting one
// Promise.all failure wipe out both means a broken AWS session still shows "DB health: OK,
// Top paths: <AWS error>" instead of a single opaque failure that could be either side.
async function loadTopPathsSection (stage: Stage, startTime: number, endTime: number): Promise<Section<TopPath[]>> {
  try {
    const nginxLogGroupName = await resolveNginxLogGroupName(stage)
    const topPaths = await queryTopPaths(nginxLogGroupName, startTime, endTime)
    return { data: topPaths, error: null }
  } catch (error) {
    return { data: null, error: classifyError(error) }
  }
}

async function loadDbHealthSection (): Promise<Section<DbHealthSnapshot>> {
  try {
    const dbHealth = await getDbHealthSnapshot()
    return { data: dbHealth, error: null }
  } catch (error) {
    return { data: null, error: classifyError(error) }
  }
}

// Demo branches only ever deploy to the dev AWS account (config.py's 'demo'
// environment uses catalog_dev, same as 'dev' - see AWS_REGION/Stage comments
// above) - skipping the CloudFormation call entirely for 'production' avoids
// a pointless cross-account lookup that would just come back empty (or error,
// if the session isn't even authenticated against the dev account).
async function loadDemosSection (stage: Stage): Promise<Section<DemoDeployment[]>> {
  if (stage !== 'dev') {
    return { data: [], error: null }
  }
  try {
    const demos = await queryDemoDeployments()
    return { data: demos, error: null }
  } catch (error) {
    return { data: null, error: classifyError(error) }
  }
}

async function handleQueriesRequest (req: Request, res: Response): Promise<void> {
  const stage = resolveStage(req)
  const hours = parseHours(req.query.hours)
  const endTime = Math.floor(Date.now() / 1000)
  const startTime = endTime - Math.floor(hours * 3600)

  const [topPaths, dbHealth, demos] = await Promise.all([
    loadTopPathsSection(stage, startTime, endTime),
    loadDbHealthSection(),
    loadDemosSection(stage)
  ])

  res.json({ hours, topPaths, dbHealth, demos, stage })
}

const PANEL_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Catalog API analytics</title>
<style>
  :root {
    --ink: #1a2433;
    --muted: #5b6b82;
    --border: #dde3ec;
    --accent: #2f6fed;
    --accent-dark: #1d4fbf;
    --bg: #f3f5f9;
    --card: #ffffff;
    --error-bg: #fdecec;
    --error-border: #f3b9b9;
    --error-ink: #a3202c;
  }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    margin: 0;
    background: var(--bg);
    color: var(--ink);
  }
  header {
    background: linear-gradient(135deg, var(--accent-dark), var(--accent));
    color: #fff;
    padding: 1.5rem 2rem;
  }
  header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; }
  header p { margin: 0.25rem 0 0; color: #dce7ff; font-size: 0.85rem; }
  main { max-width: 72rem; margin: 0 auto; padding: 1.5rem 2rem 3rem; }
  .controls {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 0.6rem;
    padding: 1rem 1.25rem;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    flex-wrap: wrap;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
  }
  .controls label { font-size: 0.85rem; color: var(--muted); display: flex; align-items: center; gap: 0.4rem; }
  select, input[type=number] {
    border: 1px solid var(--border);
    border-radius: 0.4rem;
    padding: 0.35rem 0.5rem;
    font-size: 0.9rem;
    background: #fff;
    color: var(--ink);
  }
  button {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 0.4rem;
    padding: 0.45rem 1.1rem;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  button:hover:not(:disabled) { background: var(--accent-dark); }
  button:disabled { opacity: 0.6; cursor: default; }
  #status { font-size: 0.85rem; color: var(--muted); margin: 0.9rem 0 0; min-height: 1.1em; }
  #status.error { color: var(--error-ink); font-weight: 600; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 0.6rem;
    padding: 1.25rem 1.25rem 1.5rem;
    margin-top: 1.5rem;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
  }
  .card h2 { margin: 0 0 0.75rem; font-size: 1.05rem; font-weight: 600; }
  .card .hint { margin: 0 0 0.75rem; font-size: 0.82rem; color: var(--muted); }
  table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; font-size: 0.85rem; table-layout: fixed; }
  th, td { padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--border); overflow: hidden; }
  th {
    background: #f7f9fc;
    color: var(--muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-weight: 600;
  }
  tbody tr:hover { background: #f7f9fc; }
  /* table-layout: fixed needs explicit column widths - without them, a long
     unbreakable collapsible summary (e.g. bind vars JSON) makes the browser's
     auto column-sizing blow the column (and the whole table) out to fit the
     full un-wrapped text, instead of respecting the ellipsis truncation below. */
  #topPaths th:nth-child(1) { width: 24%; }
  #topPaths th:nth-child(2) { width: 8%; }
  #topPaths th:nth-child(3), #topPaths th:nth-child(4), #topPaths th:nth-child(5), #topPaths th:nth-child(6) { width: 9%; }
  #topPaths th:nth-child(7) { width: 32%; }
  #slowQueries th:nth-child(1) { width: 14%; }
  #slowQueries th:nth-child(2) { width: 10%; }
  #slowQueries th:nth-child(3) { width: 8%; }
  #slowQueries th:nth-child(4), #slowQueries th:nth-child(5) { width: 34%; }
  #demos th:nth-child(1) { width: 22%; }
  #demos th:nth-child(2) { width: 16%; }
  #demos th:nth-child(3) { width: 26%; }
  #demos th:nth-child(4), #demos th:nth-child(5) { width: 18%; }
  details { max-width: 100%; }
  details summary {
    display: block;
    cursor: pointer;
    font-family: 'SF Mono', Menlo, monospace;
    font-size: 0.8rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--accent-dark);
    list-style: none;
  }
  /* display: block (needed above so the ellipsis truncation has a width to clip
     against) suppresses the browser's native disclosure-triangle marker, which
     only renders for the default display: list-item - replacing it with our own. */
  details summary::-webkit-details-marker { display: none; }
  details summary::before { content: '▶ '; }
  details[open] summary::before { content: '▼ '; }
  details pre {
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 220px;
    overflow: auto;
    background: #f7f9fc;
    border: 1px solid var(--border);
    border-radius: 0.4rem;
    padding: 0.6rem;
    margin-top: 0.4rem;
    font-size: 0.78rem;
  }
  .error {
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    color: var(--error-ink);
    border-radius: 0.4rem;
    padding: 0.6rem 0.75rem;
    font-size: 0.85rem;
  }
  .section-error { display: none; }
  .badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
  }
  .badge-ok { background: #e6f4ea; color: #1e7b34; }
  .badge-progress { background: #fff4e0; color: #9a6400; }
  .badge-bad { background: var(--error-bg); color: var(--error-ink); }
  .badge-warn { background: #fff0d6; color: #946200; }
  a { color: var(--accent-dark); }
  /* ~15 single-line rows before scrolling kicks in - approximate, since rows
     with an opened <details> or wrapped text are taller than one line. */
  .table-wrap { max-height: 34rem; overflow-y: auto; }
  .table-wrap.expanded { max-height: none; overflow-y: visible; }
  .table-wrap thead th { position: sticky; top: 0; }
  .table-toggle {
    display: none;
    margin-top: 0.6rem;
    background: none;
    color: var(--accent-dark);
    border: 1px solid var(--border);
    border-radius: 0.4rem;
    padding: 0.3rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 600;
  }
  .table-toggle:hover { background: #f7f9fc; }
</style>
</head>
<body>
<header>
  <h1>Catalog API analytics</h1>
  <p>Popular request paths (CloudWatch), ArangoDB health, and active demo deployments.</p>
</header>
<main>
  <div class="controls">
    <label>Stage
      <select id="stage"><option value="dev">dev</option><option value="production">production</option></select>
    </label>
    <label>Hours
      <input type="number" id="hours" value="24" style="width: 4rem">
    </label>
    <button id="load">Load</button>
  </div>
  <p id="status"></p>
  <section class="card">
    <h2>Top paths</h2>
    <p id="topPathsError" class="error section-error"></p>
    <div class="table-wrap" id="topPathsWrap">
      <table id="topPaths">
        <thead><tr><th>Path</th><th>Hits</th><th>Avg (s)</th><th>Min (s)</th><th>Max (s)</th><th>p95 (s)</th><th>Popular calls</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <button type="button" class="table-toggle" id="topPathsToggle"></button>
  </section>
  <section class="card">
    <h2>DB health during this window</h2>
    <p id="dbHealthError" class="error section-error"></p>
    <p class="hint">Queue time (ArangoDB backlog signal) - latest: <span id="queueLatest"></span>s, avg: <span id="queueAvg"></span>s</p>
    <div class="table-wrap" id="slowQueriesWrap">
      <table id="slowQueries">
        <thead><tr><th>Started</th><th>Run time (s)</th><th>State</th><th>Query</th><th>Bind vars</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <button type="button" class="table-toggle" id="slowQueriesToggle"></button>
  </section>
  <section class="card" id="demosCard">
    <h2>Demo deployments</h2>
    <p class="hint">Demo branches only exist in the dev AWS account - this section is hidden for the production stage.</p>
    <p id="demosError" class="error section-error"></p>
    <div class="table-wrap" id="demosWrap">
      <table id="demos">
        <thead><tr><th>Branch</th><th>Status</th><th>Age / TTL</th><th>Created</th><th>Last updated</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <button type="button" class="table-toggle" id="demosToggle"></button>
  </section>
</main>
<script>
function esc (value) {
  return String(value).replace(/[&<>"']/g, function (ch) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
  })
}

function truncateOneLine (text, maxLen) {
  const oneLine = text.replace(/\\s+/g, ' ').trim()
  return oneLine.length > maxLen ? oneLine.slice(0, maxLen) + '...' : oneLine
}

// summaryLabel stays visible; clicking reveals fullText in a selectable,
// copyable <pre> - used both for truncated long text (query/bind vars) and
// for a short label that expands into unrelated full text (min/max cells).
function makeCollapsible (fullText, summaryLabel) {
  const details = document.createElement('details')
  const summary = document.createElement('summary')
  summary.textContent = summaryLabel
  const pre = document.createElement('pre')
  pre.textContent = fullText
  details.appendChild(summary)
  details.appendChild(pre)
  return details
}

// Renders a section's error (if any) into its <p class="error"> placeholder, with the
// full error detail (stack/raw message) tucked behind a collapsible so the summary stays
// readable at a glance - this is the "why is my panel blank" message the coworker needs.
function renderSectionError (errorEl, error) {
  errorEl.innerHTML = ''
  if (error == null) {
    errorEl.classList.add('section-error')
    return
  }
  errorEl.classList.remove('section-error')
  errorEl.appendChild(document.createTextNode(error.summary + ' '))
  errorEl.appendChild(makeCollapsible(error.detail, 'details'))
}

const ROWS_VISIBLE_COLLAPSED = 15

// Wires the click handler once per table (idempotent across repeated Load
// clicks, since this only runs at script init - see setupTableToggle calls
// below) - the actual expand/collapse state always resets on new data via
// updateTableToggle so a stale "expanded" table doesn't carry over for an
// unrelated row count.
function setupTableToggle (wrapId, toggleId) {
  const wrap = document.getElementById(wrapId)
  const toggle = document.getElementById(toggleId)
  toggle.addEventListener('click', () => {
    const expanded = wrap.classList.toggle('expanded')
    toggle.textContent = expanded ? 'Show fewer rows' : toggle.dataset.expandLabel
  })
}

function updateTableToggle (wrapId, toggleId, rowCount) {
  const wrap = document.getElementById(wrapId)
  const toggle = document.getElementById(toggleId)
  wrap.classList.remove('expanded')
  if (rowCount > ROWS_VISIBLE_COLLAPSED) {
    toggle.dataset.expandLabel = 'Show all ' + rowCount + ' rows'
    toggle.textContent = toggle.dataset.expandLabel
    toggle.style.display = 'inline-block'
  } else {
    toggle.style.display = 'none'
  }
}

function renderTopPaths (topPaths) {
  const tbody = document.querySelector('#topPaths tbody')
  tbody.innerHTML = ''
  for (const row of topPaths) {
    const tr = document.createElement('tr')
    tr.innerHTML = '<td>' + esc(row.urlpath) + '</td><td>' + row.hits + '</td><td>' +
      row.avgSeconds.toFixed(3) + '</td>'

    const minCell = document.createElement('td')
    const minEndpoint = row.urlpath + (row.minExampleQuerystring ? '?' + row.minExampleQuerystring : '')
    minCell.appendChild(makeCollapsible(minEndpoint, row.minSeconds.toFixed(3)))
    tr.appendChild(minCell)

    const maxCell = document.createElement('td')
    const maxEndpoint = row.urlpath + (row.maxExampleQuerystring ? '?' + row.maxExampleQuerystring : '')
    maxCell.appendChild(makeCollapsible(maxEndpoint, row.maxSeconds.toFixed(3)))
    tr.appendChild(maxCell)

    const p95Cell = document.createElement('td')
    p95Cell.textContent = row.p95Seconds.toFixed(3)
    tr.appendChild(p95Cell)

    const callsCell = document.createElement('td')
    if (row.topCalls.length > 0) {
      const summaryLabel = row.topCalls.length + ' repeated call(s)'
      const fullText = row.topCalls.map(function (call) {
        return '(' + call.hits + 'x, avg ' + call.avgSeconds.toFixed(3) + 's) ?' + call.querystring
      }).join('\\n')
      callsCell.appendChild(makeCollapsible(fullText, summaryLabel))
    } else {
      callsCell.textContent = 'no repeated calls in this window'
    }
    tr.appendChild(callsCell)
    tbody.appendChild(tr)
  }
  updateTableToggle('topPathsWrap', 'topPathsToggle', topPaths.length)
}

function renderDbHealth (dbHealth) {
  document.getElementById('queueLatest').textContent = String(dbHealth.queueTimeLatest ?? 'n/a')
  document.getElementById('queueAvg').textContent = dbHealth.queueTimeAvg.toFixed(3)

  const tbody = document.querySelector('#slowQueries tbody')
  tbody.innerHTML = ''
  for (const q of dbHealth.slowQueries) {
    const tr = document.createElement('tr')

    const startedCell = document.createElement('td')
    startedCell.textContent = q.started
    const runTimeCell = document.createElement('td')
    runTimeCell.textContent = q.runTime.toFixed(3)
    const stateCell = document.createElement('td')
    stateCell.textContent = q.state

    const queryCell = document.createElement('td')
    queryCell.appendChild(makeCollapsible(q.query, truncateOneLine(q.query, 80)))

    const bindVarsCell = document.createElement('td')
    const bindVarsText = JSON.stringify(q.bindVars)
    bindVarsCell.appendChild(makeCollapsible(bindVarsText, truncateOneLine(bindVarsText, 60)))

    tr.appendChild(startedCell)
    tr.appendChild(runTimeCell)
    tr.appendChild(stateCell)
    tr.appendChild(queryCell)
    tr.appendChild(bindVarsCell)
    tbody.appendChild(tr)
  }
  updateTableToggle('slowQueriesWrap', 'slowQueriesToggle', dbHealth.slowQueries.length)
}

function demoStatusBadgeClass (status) {
  if (status.endsWith('_FAILED') || status.includes('ROLLBACK')) {
    return 'badge-bad'
  }
  if (status.endsWith('_IN_PROGRESS')) {
    return 'badge-progress'
  }
  return 'badge-ok'
}

function formatTimestamp (isoString) {
  return isoString ? new Date(isoString).toLocaleString() : 'n/a'
}

function renderDemos (demos) {
  const tbody = document.querySelector('#demos tbody')
  tbody.innerHTML = ''
  for (const demo of demos) {
    const tr = document.createElement('tr')

    const branchCell = document.createElement('td')
    if (demo.url) {
      const link = document.createElement('a')
      link.href = demo.url
      link.target = '_blank'
      link.rel = 'noopener noreferrer'
      link.textContent = demo.branch
      branchCell.appendChild(link)
    } else {
      branchCell.textContent = demo.branch
    }
    tr.appendChild(branchCell)

    const statusCell = document.createElement('td')
    const statusBadge = document.createElement('span')
    statusBadge.className = 'badge ' + demoStatusBadgeClass(demo.status)
    statusBadge.textContent = demo.status
    statusCell.appendChild(statusBadge)
    tr.appendChild(statusCell)

    const ttlCell = document.createElement('td')
    if (demo.ageHours != null) {
      const ageText = demo.ageHours.toFixed(1) + 'h old' + (demo.ttlHours != null ? ' / ' + demo.ttlHours + 'h TTL' : '')
      ttlCell.appendChild(document.createTextNode(ageText + ' '))
      if (demo.pastTtl) {
        const pastTtlBadge = document.createElement('span')
        pastTtlBadge.className = 'badge badge-warn'
        pastTtlBadge.textContent = 'past TTL'
        ttlCell.appendChild(pastTtlBadge)
      }
      if (demo.turnOffOnFridayNight) {
        ttlCell.appendChild(document.createTextNode(' '))
        const fridayBadge = document.createElement('span')
        fridayBadge.className = 'badge badge-progress'
        fridayBadge.textContent = 'off Fri night'
        ttlCell.appendChild(fridayBadge)
      }
    } else {
      ttlCell.textContent = 'n/a'
    }
    tr.appendChild(ttlCell)

    const createdCell = document.createElement('td')
    createdCell.textContent = formatTimestamp(demo.createdAt)
    tr.appendChild(createdCell)

    const updatedCell = document.createElement('td')
    updatedCell.textContent = formatTimestamp(demo.updatedAt)
    tr.appendChild(updatedCell)

    tbody.appendChild(tr)
  }
  updateTableToggle('demosWrap', 'demosToggle', demos.length)
}

setupTableToggle('topPathsWrap', 'topPathsToggle')
setupTableToggle('slowQueriesWrap', 'slowQueriesToggle')
setupTableToggle('demosWrap', 'demosToggle')

const loadButton = document.getElementById('load')

loadButton.addEventListener('click', async () => {
  const hours = document.getElementById('hours').value
  const stage = document.getElementById('stage').value
  const statusEl = document.getElementById('status')
  statusEl.classList.remove('error')
  statusEl.textContent = 'Querying CloudWatch Logs Insights and ArangoDB - this can take up to ~30s...'
  loadButton.disabled = true
  try {
    const response = await fetch('/internal/analytics/queries?hours=' + encodeURIComponent(hours) + '&stage=' + encodeURIComponent(stage))
    if (!response.ok) {
      statusEl.classList.add('error')
      const body = await response.json().catch(() => null)
      statusEl.textContent = body && body.error
        ? 'Request failed (' + response.status + '): ' + body.error.summary
        : 'Request failed: ' + response.status
      return
    }
    const data = await response.json()

    const topPathsErrorEl = document.getElementById('topPathsError')
    renderSectionError(topPathsErrorEl, data.topPaths.error)
    renderTopPaths(data.topPaths.data ?? [])

    const dbHealthErrorEl = document.getElementById('dbHealthError')
    renderSectionError(dbHealthErrorEl, data.dbHealth.error)
    renderDbHealth(data.dbHealth.data ?? { queueTimeLatest: null, queueTimeAvg: NaN, slowQueries: [] })

    const demosCardEl = document.getElementById('demosCard')
    demosCardEl.style.display = data.stage === 'dev' ? '' : 'none'
    if (data.stage === 'dev') {
      const demosErrorEl = document.getElementById('demosError')
      renderSectionError(demosErrorEl, data.demos.error)
      renderDemos(data.demos.data ?? [])
    }

    const totalSections = data.stage === 'dev' ? 3 : 2
    const sectionErrors = [data.topPaths.error, data.dbHealth.error, data.stage === 'dev' ? data.demos.error : null].filter(Boolean)
    if (sectionErrors.length === totalSections) {
      statusEl.classList.add('error')
      statusEl.textContent = 'All sections failed to load - see the error messages above for details.'
    } else if (sectionErrors.length > 0) {
      statusEl.textContent = 'Loaded with ' + sectionErrors.length + ' section(s) failing - see the error message(s) above for details.'
    } else {
      statusEl.textContent = 'Loaded ' + data.topPaths.data.length + ' path(s) for the last ' + data.hours + ' hour(s).'
    }
  } catch (error) {
    statusEl.classList.add('error')
    statusEl.textContent = 'Request failed: ' + error
  } finally {
    loadButton.disabled = false
  }
})
</script>
</body>
</html>`

export const internalAnalyticsRouter = Router()

internalAnalyticsRouter.get('/', (_req, res) => {
  res.type('html').send(PANEL_HTML)
})

internalAnalyticsRouter.get('/queries', (req, res) => {
  handleQueriesRequest(req, res).catch((error) => {
    console.error('Failed to build analytics snapshot', error)
    res.status(500).json({ error: classifyError(error) })
  })
})
