"""
Coding Harness for Cloudkot
Core coding logic and functionality
"""

import json

from api_client import APIClient, Message, ChatResult
from satire.engine import SatireEngine
from satire.forms import FormGenerator
from tools import get_tool_definitions, execute_tool, list_tools


MAX_TOOL_ITERATIONS = 10


class CodingHarness:
    def __init__(self, api_client: APIClient, satire_engine: SatireEngine):
        self.api = api_client
        self.satire = satire_engine
        self.form_generator = FormGenerator()

    async def _run_agent_loop(self, messages: list[Message], context: str | None = None) -> str:
        """Run the tool-calling agent loop.
        
        Sends messages with tool definitions, handles tool calls by executing
        tools and feeding results back, until the model returns a final response.
        """
        tool_defs = get_tool_definitions()
        available_tools = list_tools()
        
        # Build a system-level message explaining tools if they exist
        system_msg = Message(
            role="system",
            content=(
                "You are a helpful coding assistant with access to filesystem tools. "
                f"You have access to the following tools: {', '.join(available_tools)}. "
                "Use them to explore the codebase, read files, and gather context before answering. "
                "You can also run shell commands to execute code or get information."
            )
        )
        if not any(msg.role == "system" for msg in messages):
            messages = [system_msg] + messages

        for iteration in range(MAX_TOOL_ITERATIONS):
            result = await self.api.chat(messages, use_context=False, tools=tool_defs)

            if result.tool_calls:
                # Create ONE assistant message with ALL tool calls grouped together
                tool_calls_list = [{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    }
                } for tc in result.tool_calls]
                
                messages.append(Message(
                    role="assistant",
                    content=None,
                    tool_calls=tool_calls_list,
                ))
                
                # Execute each tool and add individual tool result messages
                for tc in result.tool_calls:
                    tool_output = await execute_tool(tc.name, tc.arguments)
                    messages.append(Message(
                        role="tool",
                        content=tool_output,
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))
                
                continue  # Go to next iteration

            # No tool calls — return the content
            if result.content:
                return self.satire.wrap_response(result.content, context)
            
            return self.satire.wrap_response("(No response generated)", context)

        return self.satire.wrap_response(
            "(Reached maximum tool call iterations without a final response)", context
        )

    async def generate_code(self, prompt: str, context: str | None = None) -> str:
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, context)

    async def explain_code(self, code: str) -> str:
        prompt = f"Erkläre diesen Code auf Deutsch. Sei präzise und technisch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "code explanation")

    async def check_code(self, code: str) -> str:
        prompt = f"Analysiere diesen Code auf Fehler und verbessere ihn. Antworte auf Deutsch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "code review")

    async def refactor_code(self, code: str) -> str:
        prompt = f"Refactoriere diesen Code nach besten Praktiken. Nutze deutsche Kommentare:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "refactor")

    async def generate_form(self, code: str, form_type: str) -> str:
        return self.form_generator.generate_form(form_type, code)
