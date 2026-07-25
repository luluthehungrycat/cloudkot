"""
MCP (Model Context Protocol) Server for Cloudkot
Provides MCP server functionality for integrating with MCP clients
"""

import json
from typing import Any

import websockets
from pydantic import BaseModel


class MCPMessage(BaseModel):
    """Base MCP message"""

    jsonrpc: str = "2.0"
    id: int | None = None
    method: str | None = None
    params: dict[str, Any] | None = None


class MCPServer:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
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

    async def handle_connection(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ):
        """Handle a new WebSocket connection"""
        self.connections.append(websocket)
        print(f"MCP client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                response = await self.handle_message(message)
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            print("MCP client disconnected")
        finally:
            self.connections.remove(websocket)

    async def start(self):
        """Start the MCP server"""
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
        )
        print(f"MCP server started on ws://{self.host}:{self.port}")

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


# Singleton instance
mcp_server = MCPServer()
