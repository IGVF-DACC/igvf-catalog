"""IGVF Catalog MCP Server entry point."""

import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

# Import tools
from .tools.get_entity import GET_ENTITY_TOOL, get_entity
from .tools.search_region import SEARCH_REGION_TOOL, search_region
from .tools.find_associations import FIND_ASSOCIATIONS_TOOL, find_associations
from .tools.resolve_id import RESOLVE_ID_TOOL, resolve_id
from .tools.list_sources import LIST_SOURCES_TOOL, list_sources

# Import resources
from .resources.schemas import ALL_RESOURCES, get_resource_content


# Configuration
API_URL = os.getenv('IGVF_CATALOG_API_URL', 'https://api.catalog.igvf.org')

# Create MCP server instance
app = Server('igvf-catalog-mcp')


# Register tools
@app.list_tools()
async def list_tools():
    """List available tools."""
    return [
        GET_ENTITY_TOOL,
        SEARCH_REGION_TOOL,
        FIND_ASSOCIATIONS_TOOL,
        RESOLVE_ID_TOOL,
        LIST_SOURCES_TOOL,
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a tool by name."""
    if name == 'get_entity':
        return await get_entity(arguments)
    elif name == 'search_region':
        return await search_region(arguments)
    elif name == 'find_associations':
        return await find_associations(arguments)
    elif name == 'resolve_id':
        return await resolve_id(arguments)
    elif name == 'list_sources':
        return await list_sources(arguments)
    else:
        raise ValueError(f'Unknown tool: {name}')


# Register resources
@app.list_resources()
async def list_resources():
    """List available resources."""
    return ALL_RESOURCES


@app.read_resource()
async def read_resource(uri: str):
    """Read a resource by URI."""
    content = await get_resource_content(uri)
    return [TextContent(type='text', text=content)]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
