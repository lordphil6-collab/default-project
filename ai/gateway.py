"""Provider-agnostic LLM gateway - Phase 0 stub.

Phase 4+ will enforce JSON-schema outputs, confidence scores,
versioned prompts in ai/prompts/v*, eval fixtures.
No raw LLM strings are persisted.
"""

PROVIDERS = ("none", "gemini-flash", "gpt-4o-mini", "ollama")


def extract_json(prompt_version: str, payload: dict) -> dict:
    raise NotImplementedError("Phase 4: implement gateway + evals")
