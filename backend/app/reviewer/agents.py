"""Agent construction for the reviewer pipeline.

We use Microsoft Agent Framework as the orchestration layer. For the tracer
bullet's two-step flow, plain async composition is sufficient — we do NOT
use Agent Framework's graph-based Workflows feature here.

Agent Framework's `AnthropicFoundryClient` wraps Anthropic's AnthropicFoundry
SDK client internally. It picks up ANTHROPIC_FOUNDRY_API_KEY and
ANTHROPIC_FOUNDRY_RESOURCE from env automatically. For eventual production,
unset the API key and let it fall back to DefaultAzureCredential.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.reviewer.pack_loader import Pack


@dataclass(frozen=True)
class AgentHandle:
    """A thin wrapper so callers don't depend on the underlying SDK shape.

    Call `await handle.run(user_message)` to get the raw text response.
    """

    name: str
    model: str
    temperature: float
    max_tokens: int
    instructions: str
    _agent: Any  # underlying agent-framework agent

    async def run(self, user_message: str) -> str:
        """Invoke the agent and return the plain text of the response.

        Agent Framework's agent.run() returns an AgentRunResponse whose
        .text property is the concatenated assistant text. We expose only
        the string because structured-output parsing happens in the pipeline.
        """
        result = await self._agent.run(
            user_message,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        # AgentRunResponse exposes .text; fall back to str() if shape differs.
        text = getattr(result, "text", None)
        if text is None:
            text = str(result)
        return text


def _build_client() -> Any:
    """Construct the AnthropicFoundryClient.

    Env vars (ANTHROPIC_FOUNDRY_API_KEY, ANTHROPIC_FOUNDRY_RESOURCE) are
    picked up by the SDK automatically.
    """
    # Imported lazily so tests that don't exercise the LLM path don't require
    # the dependency to be installed.
    from agent_framework.foundry import AnthropicFoundryClient  # type: ignore

    return AnthropicFoundryClient()


def _build_agent(
    name: str,
    instructions: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> AgentHandle:
    client = _build_client()
    agent = client.create_agent(name=name, instructions=instructions)
    return AgentHandle(
        name=name,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        instructions=instructions,
        _agent=agent,
    )


def build_reviewer_agent(pack: Pack, rendered_instructions: str) -> AgentHandle:
    """Reviewer agent: temperature=1.0 for multi-shot diversity."""
    model = pack.models.reviewer or settings.FOUNDRY_REVIEWER_MODEL
    return _build_agent(
        name=f"reviewer:{pack.id}",
        instructions=rendered_instructions,
        model=model,
        temperature=settings.REVIEWER_TEMPERATURE,
        max_tokens=4096,
    )


def build_consolidator_agent(pack: Pack, rendered_instructions: str) -> AgentHandle:
    """Consolidator agent: low temperature for determinism."""
    model = pack.models.consolidator or settings.FOUNDRY_CONSOLIDATOR_MODEL
    return _build_agent(
        name=f"consolidator:{pack.id}",
        instructions=rendered_instructions,
        model=model,
        temperature=settings.CONSOLIDATOR_TEMPERATURE,
        max_tokens=8192,
    )
