"""
Coding Harness for Cloudkot
Core coding logic and functionality
"""

from api_client import APIClient, Message
from satire.engine import SatireEngine
from satire.forms import FormGenerator


class CodingHarness:
    def __init__(self, api_client: APIClient, satire_engine: SatireEngine):
        self.api = api_client
        self.satire = satire_engine
        self.form_generator = FormGenerator()

    async def generate_code(self, prompt: str, context: str | None = None) -> str:
        messages = [Message(role="user", content=prompt)]
        llm_response = await self.api.chat(messages)
        return self.satire.wrap_response(llm_response, context)

    async def explain_code(self, code: str) -> str:
        prompt = f"Erkläre diesen Code auf Deutsch. Sei präzise und technisch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        llm_response = await self.api.chat(messages)
        return self.satire.wrap_response(llm_response, "code explanation")

    async def check_code(self, code: str) -> str:
        prompt = f"Analysiere diesen Code auf Fehler und verbessere ihn. Antworte auf Deutsch:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        llm_response = await self.api.chat(messages)
        return self.satire.wrap_response(llm_response, "code review")

    async def refactor_code(self, code: str) -> str:
        prompt = f"Refactoriere diesen Code nach besten Praktiken. Nutze deutsche Kommentare:\n\n{code}"
        messages = [Message(role="user", content=prompt)]
        llm_response = await self.api.chat(messages)
        return self.satire.wrap_response(llm_response, "refactor")

    async def generate_form(self, code: str, form_type: str) -> str:
        return self.form_generator.generate_form(form_type, code)
