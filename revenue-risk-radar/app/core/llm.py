from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

import certifi

from app.core.settings import get_settings


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider(self) -> str:
        provider = self.settings.llm_provider
        if provider not in {"groq", "gemini"}:
            return "none"
        return provider

    def configured(self) -> bool:
        if self.provider == "groq":
            return bool(self.settings.groq_api_key)
        if self.provider == "gemini":
            return bool(self.settings.gemini_api_key)
        return False

    def required_env_var(self) -> str:
        if self.provider == "gemini":
            return "GEMINI_API_KEY"
        if self.provider == "groq":
            return "GROQ_API_KEY"
        return "LLM_PROVIDER"

    def configuration_hint(self) -> str:
        if self.provider == "gemini":
            return "Set LLM_PROVIDER=gemini and GEMINI_API_KEY in the deployment environment."
        if self.provider == "groq":
            return "Set LLM_PROVIDER=groq and GROQ_API_KEY in the deployment environment."
        return "Set LLM_PROVIDER to groq or gemini, then add the matching API key."

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 700) -> str:
        if not self.configured():
            return self._fallback_answer(user_prompt)
        if self.provider == "groq":
            return self._complete_groq(system_prompt, user_prompt, max_tokens)
        if self.provider == "gemini":
            return self._complete_gemini(system_prompt, user_prompt, max_tokens)
        return self._fallback_answer(user_prompt)

    def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(request, timeout=45, context=context) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM provider returned {exc.code}: {detail}") from exc

    def _complete_groq(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_completion_tokens": max_tokens,
        }
        response = self._post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload,
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "User-Agent": "revenue-risk-radar/1.0",
            },
        )
        return response["choices"][0]["message"]["content"].strip()

    def _complete_gemini(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": max_tokens,
            },
        }
        response = self._post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent",
            payload,
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-goog-api-key": self.settings.gemini_api_key,
                "User-Agent": "revenue-risk-radar/1.0",
            },
        )
        parts = response["candidates"][0]["content"].get("parts", [])
        return "\n".join(part.get("text", "") for part in parts).strip()

    def _fallback_answer(self, user_prompt: str) -> str:
        return (
            "AI provider is not configured for this deployment. "
            "The KPI dashboard, risk scoring, access scoping, and hotel metrics are still live. "
            f"{self.configuration_hint()} Restart the server after saving the secret."
        )


def build_business_prompt(question: str, pack: dict[str, Any], policy: dict[str, Any]) -> tuple[str, str]:
    system_prompt = """
You are a hotel revenue intelligence copilot.
Use only the provided analytics JSON. Do not invent numbers, hotels, chains, or dates.
If the selected profile is partner-scoped, never discuss data outside the applied scope.
Answer like a concise business analyst: state the finding, explain the driver, and recommend one next action.
""".strip()

    user_prompt = f"""
User question:
{question}

Applied access profile:
{json.dumps(policy, default=str)}

Analytics JSON:
{json.dumps(pack, default=str)}
""".strip()

    return system_prompt, user_prompt
