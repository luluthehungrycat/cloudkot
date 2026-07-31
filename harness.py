"""
Coding Harness for Cloudkot
Core coding logic and functionality
"""

import asyncio
import json
from typing import Any

from api_client import APIClient, Message
from satire.engine import SatireEngine
from satire.forms import FormGenerator
from skills.skill_manager import skill_manager
from tools import execute_tool, get_tool_definitions, list_tools

MAX_TOOL_ITERATIONS = 10


class CodingHarness:
    def __init__(self, api_client: APIClient, satire_engine: SatireEngine):
        self.api = api_client
        self.satire = satire_engine
        self.form_generator = FormGenerator()
        self.skill_manager = skill_manager

    async def _run_agent_loop(
        self, 
        messages: list[Message], 
        context: str | None = None, 
        callbacks=None,
        skills: list[str] | None = None
    ) -> str:
        """Run the tool-calling agent loop with optional skills.

        Sends messages with tool definitions, handles tool calls by executing
        tools and feeding results back, until the model returns a final response.

        When callbacks are provided, streaming is enabled for real-time display.
        When skills are provided, they are executed at pre- and post-processing stages.
        """
        tool_defs = get_tool_definitions()
        available_tools = list_tools()

        # Build a system-level message explaining tools if they exist
        system_msg = Message(
            role="system",
            content=(
                "Sachbearbeiter-KI-Assistent gemäß §28 Abs. 4 der KI-Verordnung (KI-VO). "
                f"Zugelassene Hilfsmittel (§5 Abs. 1): {', '.join(available_tools)}. "
                "Jede Nutzung der Hilfsmittel ist formpflichtig und wird gemäß §12 Abs. 3 protokolliert. "
                "Verwenden Sie die genehmigten Werkzeuge zur Sichtung der Aktenlage. "
                "Der Antragsteller erwartet einen geprüften Bescheid nach DIN 66234-8. "
                "Ordnungswidrigkeiten (§89 OWiG) werden mit einem Formularverweis geahndet. "
                "Bitte legen Sie zu jeder Aktion das entsprechende Formular vor. "
                "Bei Rückfragen wenden Sie sich an Herrn Schmidt, Raum 304."
            )
        )
        if not any(msg.role == "system" for msg in messages):
            messages = [system_msg] + messages

        for iteration in range(MAX_TOOL_ITERATIONS):
            # Pre-process with skills
            if skills:
                messages = await self._apply_skills_preprocess(messages, context, skills)

            if callbacks:
                result = await self.api.chat(messages, use_context=False, tools=tool_defs, stream=True, callbacks=callbacks)
            else:
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

                # Execute each tool with timeout
                for tc in result.tool_calls:
                    if callbacks and callbacks.on_tool_call:
                        callbacks.on_tool_call(tc.name, tc.arguments)

                    try:
                        tool_output = await asyncio.wait_for(
                            execute_tool(tc.name, tc.arguments),
                            timeout=30.0
                        )
                    except asyncio.TimeoutError:
                        tool_output = f"Error: Tool '{tc.name}' timed out after 30 seconds"
                    except Exception as e:
                        tool_output = f"Error executing tool '{tc.name}': {e}"

                    if callbacks and callbacks.on_tool_result:
                        callbacks.on_tool_result(tc.name, tool_output)

                    messages.append(Message(
                        role="tool",
                        content=tool_output,
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))

                continue  # Go to next iteration

            # No tool calls — return the content
            if result.content:
                # Post-process with skills
                if skills:
                    result.content = await self._apply_skills_postprocess(
                        result.content, messages, context, skills
                    )
                return self.satire.wrap_response(result.content, context)

            return self.satire.wrap_response("(No response generated)", context)

        return self.satire.wrap_response(
            "(Reached maximum tool call iterations without a final response)", context
        )

    async def _apply_skills_preprocess(
        self, messages: list[Message], context: str | None, skills: list[str]
    ) -> list[Message]:
        """Apply pre-processing skills to messages before LLM call."""
        for skill_name in skills:
            if self.skill_manager.can_execute_skill(skill_name):
                skill_result = await self.skill_manager.execute_skill(
                    skill_name,
                    messages=messages,
                    context=context,
                    phase="preprocess"
                )
                if skill_result.success and skill_result.output:
                    messages.append(Message(
                        role="system",
                        content=f"[Skill {skill_name} preprocess]: {skill_result.output}"
                    ))
        return messages

    async def _apply_skills_postprocess(
        self, content: str, messages: list[Message], context: str | None, skills: list[str]
    ) -> str:
        """Apply post-processing skills to LLM output."""
        for skill_name in skills:
            if self.skill_manager.can_execute_skill(skill_name):
                skill_result = await self.skill_manager.execute_skill(
                    skill_name,
                    content=content,
                    messages=messages,
                    context=context,
                    phase="postprocess"
                )
                if skill_result.success and skill_result.output:
                    content += f"\n\n[Skill {skill_name}]: {skill_result.output}"
        return content

    async def generate_code(self, prompt: str, context: str | None = None, skills: list[str] | None = None) -> str:
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, context, skills=skills)

    async def generate_code_stream(self, prompt: str, context: str | None = None, callbacks=None, skills: list[str] | None = None) -> str:
        """Generate code with streaming callbacks for real-time display."""
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, context, callbacks=callbacks, skills=skills)

    async def continue_chat(self, messages: list[Message], context: str | None = None, skills: list[str] | None = None) -> str:
        """Continue a conversation with existing message history.

        Unlike generate_code() which starts fresh, this accepts the full
        accumulated message list. The new user message should already be
        appended to the list before calling this.
        """
        return await self._run_agent_loop(messages, context, skills=skills)

    async def continue_chat_stream(self, messages: list[Message], context: str | None = None, callbacks=None, skills: list[str] | None = None) -> str:
        """Continue a conversation with streaming callbacks for real-time display."""
        return await self._run_agent_loop(messages, context, callbacks=callbacks, skills=skills)

    async def explain_code(self, code: str, skills: list[str] | None = None) -> str:
        prompt = f"Erkläre diesen Code auf Deutsch. Sei präzise und technisch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "code explanation", skills=skills)

    async def check_code(self, code: str) -> str:
        prompt = f"Analysiere diesen Code auf Fehler und verbessere ihn. Antworte auf Deutsch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "code review")

    async def refactor_code(self, code: str, skills: list[str] | None = None) -> str:
        prompt = f"Refactoriere diesen Code nach besten Praktiken. Nutze deutsche Kommentare:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        return await self._run_agent_loop(messages, "refactor", skills=skills)

    async def generate_form(self, code: str, form_type: str) -> str:
        return self.form_generator.generate_form(form_type, code)
