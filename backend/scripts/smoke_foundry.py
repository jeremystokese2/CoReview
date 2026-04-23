"""Smoke test for Foundry + Agent Framework.

Run from inside the container:
    docker compose exec backend uv run python scripts/smoke_foundry.py

This verifies:
- ANTHROPIC_FOUNDRY_API_KEY + ANTHROPIC_FOUNDRY_RESOURCE (or DefaultAzureCredential) work
- agent_framework.foundry.AnthropicFoundryClient can be constructed
- The configured reviewer model accepts a basic request

Do not proceed to pipeline work until this prints a response.
"""
from __future__ import annotations

import asyncio
import sys

from app.config import settings
from app.reviewer.agents import AgentHandle


async def main() -> int:
    if not settings.ANTHROPIC_FOUNDRY_RESOURCE:
        print(
            "[smoke] ANTHROPIC_FOUNDRY_RESOURCE is not set — set it in .env",
            file=sys.stderr,
        )
        return 1
    if not settings.ANTHROPIC_FOUNDRY_API_KEY:
        print(
            "[smoke] ANTHROPIC_FOUNDRY_API_KEY is not set — will try DefaultAzureCredential",
            file=sys.stderr,
        )

    # Build a minimal agent with no pack context.
    from agent_framework.foundry import AnthropicFoundryClient  # type: ignore

    client = AnthropicFoundryClient()
    agent = client.create_agent(
        name="smoke",
        instructions=(
            "You are a concise assistant. Answer with exactly the word 'pong' "
            "and nothing else."
        ),
    )
    handle = AgentHandle(
        name="smoke",
        model=settings.FOUNDRY_REVIEWER_MODEL,
        temperature=0.0,
        max_tokens=16,
        instructions="",
        _agent=agent,
    )
    print(f"[smoke] Calling model {settings.FOUNDRY_REVIEWER_MODEL} ...")
    text = await handle.run("ping")
    print(f"[smoke] Response: {text!r}")
    if "pong" not in text.lower():
        print("[smoke] WARNING: response did not contain 'pong'", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
