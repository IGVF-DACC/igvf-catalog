import { generateOpenApiDocument } from 'trpc-openapi'
import { appRouter } from './routers/_app'
import { envData } from './env'
import { CATALOG_ENDPOINTS, OPENAPI_TAG_ORDER, PATH_TO_TAG } from './catalogEndpoints'

let baseUrl = `${envData.host.protocol}://${envData.host.hostname}:${envData.host.port}/api`
// prevents production SSL cert mismatch and use default ports
if (envData.host.port === 80 || envData.host.port === 443 || envData.environment === 'production') {
  baseUrl = `${envData.host.protocol}://${envData.host.hostname}/api`
}

export const swaggerConfig = {
  customCss: [
    '.swagger-ui .opblock-description-wrapper p,',
    '.swagger-ui .opblock-description-wrapper ul,',
    '.swagger-ui .opblock-description-wrapper li,',
    '.swagger-ui .opblock-description-wrapper strong {',
    'font-size: 18px; line-height: 1.5em;',
    '}',
    '.swagger-ui .opblock-description-wrapper p { margin: 0.35em 0; }',
    '.swagger-ui .opblock-description-wrapper ul { margin: 0.25em 0 0.75em 1.25em; padding-left: 1.25em; }',
    '.swagger-ui .opblock-description-wrapper li { margin: 0.35em 0; }',
    '.swagger-ui .opblock-description-wrapper p + ul { margin-top: 0.25em; }',
    '.swagger-ui .method-examples { margin-top: 1em; }',
    '.swagger-ui .method-example-description { margin: 0.25em 0 0.75em; }',
    '.swagger-ui .method-example-tabs { display: flex; flex-wrap: wrap; gap: 0.4em; margin: 0.5em 0 0.75em; }',
    '.swagger-ui .method-example-tab { background: #eef3fb; border: 1px solid #9fb7d7; border-radius: 4px; color: #1f2937; cursor: pointer; font-size: 15px; font-weight: 600; padding: 0.35em 0.7em; }',
    '.swagger-ui .method-example-tab.is-active { background: #61affe; border-color: #3b82c4; color: #0f172a; }',
    '.swagger-ui .method-example-panel { display: none; }',
    '.swagger-ui .method-example-panel.is-active { display: block; }',
    '.swagger-ui .method-example-panel strong { display: block; margin-bottom: 0.25em; }',
    '.swagger-ui .method-query-example { border-left: 3px solid #9fb7d7; margin: 0.75em 0; padding-left: 0.75em; }',
    '.swagger-ui .method-query-example strong { font-size: 16px; }',
    'html.dark-mode .swagger-ui .method-example-tab { background: #1f2937; border-color: #52677f; color: #e4e6e6; }',
    'html.dark-mode .swagger-ui .method-example-tab.is-active { background: #315f8f; border-color: #61affe; color: #ffffff; }',
    'html.dark-mode .swagger-ui .method-query-example { border-left-color: #52677f; }',
    'html.dark-mode .swagger-ui .opblock .opblock-description-wrapper {',
    'color: #e4e6e6;',
    '}',
    '.swagger-ui .auth-wrapper { display: none; }'
  ].join(' '),
  customJsStr: [
    '(() => {',
    '  const getTargetId = (element, attributeName) => {',
    '    const value = element.getAttribute(attributeName)',
    '    if (value) {',
    '      return value',
    '    }',
    '    return (element.textContent || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")',
    '  }',
    '',
    '  const activateMethodExample = (selectedTab) => {',
    '    const group = selectedTab.closest(".method-examples")',
    '    if (!group) {',
    '      return',
    '    }',
    '',
    '    const selectedPanel = getTargetId(selectedTab, "data-method-example-tab")',
    '    const tabs = Array.from(group.querySelectorAll(".method-example-tab"))',
    '    const panels = Array.from(group.querySelectorAll(".method-example-panel"))',
    '',
    '    tabs.forEach((tab) => {',
    '      const isActive = tab === selectedTab',
    '      tab.classList.toggle("is-active", isActive)',
    '      tab.setAttribute("aria-selected", String(isActive))',
    '    })',
    '',
    '    panels.forEach((panel) => {',
    '      const panelId = getTargetId(panel, "data-method-example-panel")',
    '      const isActive = panelId === selectedPanel',
    '      panel.classList.toggle("is-active", isActive)',
    '      panel.hidden = !isActive',
    '    })',
    '  }',
    '',
    '  document.addEventListener("click", (event) => {',
    '    const selectedTab = event.target.closest(".method-example-tab")',
    '    if (!selectedTab) {',
    '      return',
    '    }',
    '    event.preventDefault()',
    '    event.stopPropagation()',
    '    activateMethodExample(selectedTab)',
    '  }, true)',
    '',
    '  const initMethodExamples = (root = document) => {',
    '    root.querySelectorAll(".method-examples").forEach((group) => {',
    '      const tabs = Array.from(group.querySelectorAll(".method-example-tab"))',
    '      const panels = Array.from(group.querySelectorAll(".method-example-panel"))',
    '      if (tabs.length === 0 || panels.length === 0) {',
    '        return',
    '      }',
    '      tabs.forEach((tab) => {',
    '        tab.setAttribute("type", "button")',
    '        tab.setAttribute("role", "tab")',
    '      })',
    '      panels.forEach((panel) => panel.setAttribute("role", "tabpanel"))',
    '      activateMethodExample(tabs.find((tab) => tab.classList.contains("is-active")) || tabs[0])',
    '    })',
    '  }',
    '',
    '  const scheduleInit = () => window.setTimeout(() => initMethodExamples(), 0)',
    '',
    '  if (document.readyState === "loading") {',
    '    document.addEventListener("DOMContentLoaded", scheduleInit)',
    '  } else {',
    '    scheduleInit()',
    '  }',
    '  window.addEventListener("load", scheduleInit)',
    '  document.addEventListener("click", scheduleInit)',
    '',
    '  let retryCount = 0',
    '  const retry = window.setInterval(() => {',
    '    initMethodExamples()',
    '    retryCount += 1',
    '    if (retryCount > 20) {',
    '      window.clearInterval(retry)',
    '    }',
    '  }, 500)',
    '  new MutationObserver((mutations) => {',
    '    mutations.forEach((mutation) => {',
    '      mutation.addedNodes.forEach((node) => {',
    '        if (node instanceof HTMLElement) {',
    '          initMethodExamples(node)',
    '        }',
    '      })',
    '    })',
    '  }).observe(document.body, { childList: true, subtree: true })',
    '})()'
  ].join('\n'),
  swaggerOptions: {
    tryItOutEnabled: true,
    useUnsafeMarkdown: true
  }
}

const LICENSE = '\n\nData is licensed under the <a href=https://creativecommons.org/licenses/by/4.0/ target="_blank">Creative Commons license</a> and the software is licensed under the <a href=https://spdx.org/licenses/MIT.html target="_blank">MIT license</a>.'
const GENOMIC_COORDINATES = '\n\nOur database uses 0-based, half-open coordinates for genomic coordinates in the GRCh38 (human) and GRCm39 (mouse) reference genomes.'

let openApiConfig = {
  title: 'IGVF Catalog - Development',
  description: 'Development IGVF Catalog OpenAPI compliant REST API built using tRPC with Express.' + GENOMIC_COORDINATES + LICENSE,
  version: '2.0 - DEV',
  docsUrl: 'https://api-dev.catalog.igvf.org/openapi',
  baseUrl,
  tags: [...OPENAPI_TAG_ORDER]
}

if (process.env.IGVF_CATALOG_OPEN_API_CONFIG_TYPE === 'production') {
  openApiConfig = {
    title: 'IGVF Catalog',
    description: 'IGVF Catalog OpenAPI compliant REST API built using tRPC with Express.' + GENOMIC_COORDINATES + LICENSE,
    version: '1.2.0',
    docsUrl: 'https://api.catalog.igvf.org/openapi',
    baseUrl,
    tags: [...OPENAPI_TAG_ORDER]
  }
}

export const openApiDocument = generateOpenApiDocument(appRouter, openApiConfig)

// Assign Swagger section tags and reorder paths per catalog_endpoints.tsv.
// Endpoint descriptions and other OpenAPI metadata are left unchanged.
const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'trace'] as const

Object.entries(openApiDocument.paths).forEach(([path, pathItem]) => {
  if (pathItem === undefined) {
    return
  }
  const tag = PATH_TO_TAG[path]
  if (tag === undefined) {
    throw new Error(`OpenAPI path missing from catalog endpoint tag map: ${path}`)
  }
  HTTP_METHODS.forEach((method) => {
    const operation = pathItem[method]
    if (operation !== undefined) {
      operation.tags = [tag]
    }
  })
})

const newPath: typeof openApiDocument.paths = {}
const remainingPaths = new Set(Object.keys(openApiDocument.paths))

CATALOG_ENDPOINTS.forEach(({ path }) => {
  if (openApiDocument.paths[path] === undefined) {
    throw new Error(`Catalog endpoint not found in OpenAPI document: ${path}`)
  }
  newPath[path] = openApiDocument.paths[path]
  remainingPaths.delete(path)
})

if (remainingPaths.size > 0) {
  throw new Error(`OpenAPI paths not listed in catalog endpoints: ${Array.from(remainingPaths).join(', ')}`)
}

openApiDocument.paths = newPath
