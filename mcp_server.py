"""
MCP (Model Context Protocol) Server for Cloudkot
Provides MCP server functionality for integrating with MCP clients
"""

import json
import logging
from pathlib import Path
from typing import Any

import websockets
from pydantic import BaseModel

from compat import tomllib

logger = logging.getLogger(__name__)


class MCPMessage(BaseModel):
    """Base MCP message"""

    jsonrpc: str = "2.0"
    id: int | None = None
    method: str | None = None
    params: dict[str, Any] | None = None


class MCPServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        auth_key: str | None = None,
        auth_required: bool = False,
    ):
        self.host = host
        self.port = port
        self.auth_key = auth_key
        self.auth_required = auth_required
        self.server: websockets.WebSocketServer | None = None
        self.connections: list[websockets.WebSocketServerProtocol] = []
        self.tools: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}

    def register_tool(self, name: str, handler: Any, description: str = ""):
        """Register a tool that can be called via MCP"""
        self.tools[name] = {
            "handler": handler,
            "description": description,
        }

    def register_resource(self, uri: str, content: str, mime_type: str = "text/plain"):
        """Register a resource that can be accessed via MCP"""
        self.resources[uri] = {
            "content": content,
            "mime_type": mime_type,
        }

    @classmethod
    def from_config(cls, config_path: str | Path | None = None) -> "MCPServer":
        """Create MCPServer from configuration file.
        
        Args:
            config_path: Path to mcp.toml config file. If None, tries to load from
                       current directory or uses defaults.
        
        Returns:
            Configured MCPServer instance.
        """
        config: dict[str, Any] = {}
        
        # Try to load config from file
        if config_path:
            path = Path(config_path)
        else:
            path = Path("mcp.toml")
        
        if path.exists():
            with open(path, "rb") as f:
                config = tomllib.load(f)
            config = dict(config.get("default", config))
        
        # Extract configuration with defaults
        host = config.get("host", "localhost")
        port = config.get("port", 8080)
        auth_required = config.get("auth_required", False)
        auth_key = config.get("api_key") if auth_required else None
        
        return cls(
            host=host,
            port=port,
            auth_key=auth_key,
            auth_required=auth_required,
        )

    async def handle_message(self, message: str) -> str:
        """Handle an incoming MCP message"""
        try:
            msg = MCPMessage(**json.loads(message))

            if msg.method == "tools/list":
                return self._handle_tools_list(msg)
            elif msg.method == "tools/call":
                return await self._handle_tool_call(msg)
            elif msg.method == "resources/list":
                return self._handle_resources_list(msg)
            elif msg.method == "resources/read":
                return self._handle_resource_read(msg)
            else:
                return self._handle_unknown_method(msg)

        except Exception as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id if msg.id else 1,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}",
                    },
                }
            )

    def _handle_tools_list(self, msg: MCPMessage) -> str:
        """Handle tools/list request"""
        tools = []
        for name, tool in self.tools.items():
            tools.append(
                {
                    "name": name,
                    "description": tool["description"],
                }
            )

        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg.id,
                "result": {
                    "tools": tools,
                },
            }
        )

    async def _handle_tool_call(self, msg: MCPMessage) -> str:
        """Handle tools/call request"""
        if not msg.params or "name" not in msg.params:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid parameters: missing 'name'",
                    },
                }
            )

        tool_name = msg.params["name"]
        if tool_name not in self.tools:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}",
                    },
                }
            )

        tool = self.tools[tool_name]
        arguments = msg.params.get("arguments", {})

        try:
            result = await tool["handler"](**arguments)
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result),
                            }
                        ]
                    },
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}",
                    },
                }
            )

    def _handle_resources_list(self, msg: MCPMessage) -> str:
        """Handle resources/list request"""
        resources = []
        for uri in self.resources.keys():
            resources.append({"uri": uri})

        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg.id,
                "result": {
                    "resources": resources,
                },
            }
        )

    def _handle_resource_read(self, msg: MCPMessage) -> str:
        """Handle resources/read request"""
        if not msg.params or "uris" not in msg.params:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg.id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid parameters: missing 'uris'",
                    },
                }
            )

        uris = msg.params["uris"]
        contents = []

        for uri in uris:
            if uri in self.resources:
                resource = self.resources[uri]
                contents.append(
                    {
                        "uri": uri,
                        "mimeType": resource["mime_type"],
                        "text": resource["content"],
                    }
                )

        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg.id,
                "result": {
                    "contents": contents,
                },
            }
        )

    def _handle_unknown_method(self, msg: MCPMessage) -> str:
        """Handle unknown method"""
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg.id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {msg.method}",
                },
            }
        )

    async def _check_auth(self, headers: dict[str, str]) -> bool:
        """Check if the connection is authenticated.
        
        Args:
            headers: WebSocket headers from the connection.
            
        Returns:
            True if authenticated or auth not required, False otherwise.
        """
        if not self.auth_required:
            return True
        
        if self.auth_key is None:
            logger.warning("Authentication required but no auth_key configured")
            return False
        
        # Check for Authorization header (Bearer token)
        auth_header = headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()
            if provided_key == self.auth_key:
                return True
        
        # Also check for api_key in query params (for compatibility)
        # Note: websockets library doesn't expose query params directly in headers,
        # this would need to be handled at connection time with path parsing
        
        logger.warning("Authentication failed: Invalid or missing API key")
        return False

    async def handle_connection(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ):
        """Handle a new WebSocket connection with authentication check"""
        # Extract headers from the websocket
        headers = dict(websocket.request_headers)
        
        # Check authentication
        if not self._check_auth(headers):
            logger.warning(
                f"Unauthorized connection attempt from {websocket.remote_address}"
            )
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        self.connections.append(websocket)
        logger.info(f"MCP client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                response = await self.handle_message(message)
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            logger.info("MCP client disconnected")
        finally:
            self.connections.remove(websocket)

    async def start(self, config_path: str | Path | None = None):
        """Start the MCP server.
        
        Args:
            config_path: Optional path to mcp.toml config file.
                        If provided and auth is configured, it will be used.
        """
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
        )
        
        auth_status = "with authentication" if self.auth_required else "without authentication"
        logger.info(f"MCP server started on ws://{self.host}:{self.port} ({auth_status})")

        # Register default tools
        self._register_default_tools()

        async with self.server:
            await self.server.serve_forever()

    def _register_default_tools(self):
        """Register default Cloudkot tools"""
        # Code generation tool
        self.register_tool(
            name="generate_code",
            handler=self._generate_code_tool,
            description="Generate code from natural language description",
        )

        # Code explanation tool
        self.register_tool(
            name="explain_code",
            handler=self._explain_code_tool,
            description="Explain how code works",
        )

        # Register a sample resource
        self.register_resource(
            uri="cloudkot://readme",
            content="# Cloudkot MCP Server\n\nWelcome to the Cloudkot MCP server!",
            mime_type="text/markdown",
        )

    async def _generate_code_tool(self, prompt: str, language: str = "python") -> str:
        """Generate code tool implementation"""
        return f"Generated {language} code for: {prompt}"

    async def _explain_code_tool(self, code: str) -> str:
        """Explain code tool implementation"""
        return f"Explanation: This code {code[:50]}... does something useful."


def main():
    """Entry point for: cloudkot-mcp"""
    import asyncio
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    server = MCPServer.from_config()
    asyncio.run(server.start())


# Default singleton instance (backwards compatibility)
mcp_server = MCPServer()
