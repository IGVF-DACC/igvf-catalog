import base64
import json
import os
from datetime import timezone

import boto3

# Every demo stack (pipeline + frontend) is tagged with these by
# infrastructure/tags.py and infrastructure/config.py's 'demo' pipeline/environment
# configs, so we can find them all via the Resource Groups Tagging API instead of
# hardcoding a stack-naming pattern.
PROJECT_TAG = 'igvf-catalog-api'
ENVIRONMENT_TAG = 'demo'

# See infrastructure/naming.py + infrastructure/stacks/pipeline.py /
# infrastructure/stages/demo.py for how these names are constructed.
FRONTEND_STACK_SUFFIX = '-DemoDeployStage-FrontendStack'
PIPELINE_STACK_SUFFIX = '-DemoDeploymentPipelineStack'

_credentials_cache = None


def _get_credentials():
    global _credentials_cache
    if _credentials_cache is None:
        client = boto3.client('secretsmanager')
        secret_value = client.get_secret_value(
            SecretId=os.environ['CREDENTIALS_SECRET_ARN']
        )
        _credentials_cache = json.loads(secret_value['SecretString'])
    return _credentials_cache


def _is_authorized(headers):
    credentials = _get_credentials()
    auth_header = headers.get('authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(
            auth_header[len('Basic '):]).decode('utf-8')
        username, _, password = decoded.partition(':')
    except (ValueError, UnicodeDecodeError):
        return False
    return (
        username == credentials.get('username')
        and password == credentials.get('password')
    )


def _unauthorized_response():
    return {
        'statusCode': 401,
        'headers': {
            'WWW-Authenticate': 'Basic realm="IGVF Catalog Demos"',
            'Content-Type': 'text/plain',
        },
        'body': 'Unauthorized',
    }


def _isoformat(value):
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _tag_value(stack, key):
    for tag in stack.get('Tags', []):
        if tag['Key'] == key:
            return tag['Value']
    return None


def _output_value(stack, key):
    for output in stack.get('Outputs', []):
        if output['OutputKey'] == key:
            return output['OutputValue']
    return None


def _list_demo_stack_names():
    tagging_client = boto3.client('resourcegroupstaggingapi')
    paginator = tagging_client.get_paginator('get_resources')
    stack_names = []
    for page in paginator.paginate(
        ResourceTypeFilters=['cloudformation:stack'],
        TagFilters=[
            {'Key': 'project', 'Values': [PROJECT_TAG]},
            {'Key': 'environment', 'Values': [ENVIRONMENT_TAG]},
        ],
    ):
        for resource in page['ResourceTagMappingList']:
            # ARN shape: arn:aws:cloudformation:<region>:<account>:stack/<name>/<id>
            stack_names.append(resource['ResourceARN'].split('/')[1])
    return stack_names


def _describe_stack(cfn_client, stack_name):
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
    except cfn_client.exceptions.ClientError:
        return None
    stacks = response.get('Stacks') or []
    return stacks[0] if stacks else None


def _find_pipeline_physical_name(cfn_client, pipeline_stack_name):
    try:
        response = cfn_client.describe_stack_resources(
            StackName=pipeline_stack_name
        )
    except cfn_client.exceptions.ClientError:
        return None
    for resource in response.get('StackResources', []):
        if resource['ResourceType'] == 'AWS::CodePipeline::Pipeline':
            return resource['PhysicalResourceId']
    return None


def _latest_pipeline_execution(codepipeline_client, pipeline_name):
    try:
        response = codepipeline_client.list_pipeline_executions(
            pipelineName=pipeline_name,
            maxResults=1,
        )
    except codepipeline_client.exceptions.PipelineNotFoundException:
        return None
    summaries = response.get('pipelineExecutionSummaries') or []
    if not summaries:
        return None
    summary = summaries[0]
    revisions = summary.get('sourceRevisions') or []
    revision = revisions[0] if revisions else {}
    return {
        'status': summary.get('status'),
        'last_update_time': _isoformat(summary.get('lastUpdateTime')),
        'commit_hash': revision.get('revisionId'),
        'commit_url': revision.get('revisionUrl'),
        'commit_summary': revision.get('revisionSummary'),
    }


def _collect_demos():
    cfn_client = boto3.client('cloudformation')
    codepipeline_client = boto3.client('codepipeline')

    demos_by_branch = {}

    for stack_name in _list_demo_stack_names():
        stack = _describe_stack(cfn_client, stack_name)
        if stack is None:
            continue
        branch = _tag_value(stack, 'branch')
        if branch is None:
            continue
        demo = demos_by_branch.setdefault(branch, {'branch': branch})

        if stack_name.endswith(FRONTEND_STACK_SUFFIX):
            demo['url'] = _output_value(stack, 'FrontendUrl')
            demo['stack_status'] = stack.get('StackStatus')
            demo['stack_last_updated'] = _isoformat(
                stack.get('LastUpdatedTime') or stack.get('CreationTime')
            )
        elif stack_name.endswith(PIPELINE_STACK_SUFFIX):
            pipeline_name = _find_pipeline_physical_name(
                cfn_client, stack_name)
            if pipeline_name:
                demo['last_deploy'] = _latest_pipeline_execution(
                    codepipeline_client, pipeline_name
                )

    return sorted(
        demos_by_branch.values(),
        key=lambda demo: demo.get('stack_last_updated') or '',
        reverse=True,
    )


_HTML_PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IGVF Catalog Demos</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; color: #1a1a1a; background: #fafafa; }
  h1 { font-size: 1.4rem; }
  table { border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  th { background: #f0f0f0; position: sticky; top: 0; }
  tr:hover { background: #f5f5f5; }
  a { color: #0969da; text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85em; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: 600; color: #fff; }
  .badge-ready { background: #1a7f37; }
  .badge-progress { background: #9a6700; }
  .badge-failed { background: #cf222e; }
  .badge-unknown { background: #6e7781; }
  #status { color: #6e7781; font-size: 0.85rem; margin-bottom: 1rem; }
  button { cursor: pointer; }
</style>
</head>
<body>
<h1>IGVF Catalog demos</h1>
<div id="status">Loading&hellip;</div>
<table id="demos-table" style="display:none">
  <thead>
    <tr>
      <th>Branch</th>
      <th>Status</th>
      <th>URL</th>
      <th>Last deployed</th>
      <th>Commit</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>
<script>
function relativeTime(isoString) {
  if (!isoString) return 'unknown';
  const then = new Date(isoString);
  const seconds = Math.round((Date.now() - then.getTime()) / 1000);
  const units = [['day', 86400], ['hour', 3600], ['minute', 60]];
  for (const [name, secondsPerUnit] of units) {
    const value = Math.floor(seconds / secondsPerUnit);
    if (value >= 1) return `${value} ${name}${value > 1 ? 's' : ''} ago`;
  }
  return 'just now';
}

function statusBadge(demo) {
  const stackStatus = demo.stack_status || '';
  const deployStatus = (demo.last_deploy || {}).status || '';
  if (stackStatus.includes('ROLLBACK') || stackStatus.includes('FAILED') || deployStatus === 'Failed') {
    return '<span class="badge badge-failed">failed</span>';
  }
  if (stackStatus.includes('IN_PROGRESS') || deployStatus === 'InProgress') {
    return '<span class="badge badge-progress">deploying</span>';
  }
  if (stackStatus.endsWith('COMPLETE') && (deployStatus === 'Succeeded' || !deployStatus)) {
    return '<span class="badge badge-ready">ready</span>';
  }
  return '<span class="badge badge-unknown">unknown</span>';
}

function renderRow(demo) {
  const url = demo.url ? `<a href="${demo.url}" target="_blank" rel="noopener">${demo.url}</a>` : '&mdash;';
  const lastDeploy = demo.last_deploy || {};
  const commitHash = lastDeploy.commit_hash ? lastDeploy.commit_hash.slice(0, 7) : null;
  const commit = commitHash
    ? (lastDeploy.commit_url
        ? `<a href="${lastDeploy.commit_url}" target="_blank" rel="noopener"><code>${commitHash}</code></a>`
        : `<code>${commitHash}</code>`)
    : '&mdash;';
  const lastUpdated = demo.stack_last_updated;
  return `<tr>
    <td>${demo.branch}</td>
    <td>${statusBadge(demo)}</td>
    <td>${url}</td>
    <td title="${lastUpdated || ''}">${relativeTime(lastUpdated)}</td>
    <td>${commit}</td>
  </tr>`;
}

async function load() {
  const statusEl = document.getElementById('status');
  const tableEl = document.getElementById('demos-table');
  try {
    const response = await fetch('/api/demos');
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const data = await response.json();
    const demos = data.demos || [];
    if (demos.length === 0) {
      statusEl.textContent = 'No active demos found.';
      return;
    }
    tableEl.querySelector('tbody').innerHTML = demos.map(renderRow).join('');
    statusEl.textContent = `${demos.length} active demo(s) · refreshed ${new Date().toLocaleTimeString()}`;
    tableEl.style.display = '';
  } catch (error) {
    statusEl.textContent = `Failed to load demos: ${error.message}`;
  }
}

load();
setInterval(load, 60000);
</script>
</body>
</html>
'''


def handler(event, context):
    headers = {
        key.lower(): value
        for key, value in (event.get('headers') or {}).items()
    }
    if not _is_authorized(headers):
        return _unauthorized_response()

    path = (event.get('rawPath') or '/').rstrip('/')

    if path == '/api/demos':
        demos = _collect_demos()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'demos': demos}),
        }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': _HTML_PAGE,
    }
