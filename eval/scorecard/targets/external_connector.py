"""Answer target: an outside AI assistant (ChatGPT-style or Claude) with or without the Fuzzzy Law connector.

Interface only, to be wired by the connector work. A target must provide:

    info: dict                      # what was tested (assistant, model, connector on/off, connector URL)
    async answer(item) -> dict      # same record shape as the other targets:
        {"id", "message", "ts", "status": 200 | <error code>, "error": str | None, "latency_s": float,
         "body": {"response": "<final answer text>",
                  "citations": [{"code_name", "article_number", "paragraph", "article_url", "version_date"}],
                  "tool_calls": ["<connector tool names called>"]},
         "degraded": bool, "degraded_events": [str]}

Modes: "claude" (key service fuzzzy_law_anthropic) and "chatgpt" (no key planned yet), each with
connector=True (the Fuzzzy Law connector's tools offered to the assistant) or connector=False (the assistant
alone). Comparing the two runs on the same items shows what the connector adds.
The target is skipped cleanly when its key is absent.
"""
from __future__ import annotations


class ExternalConnectorTarget:
    name = "external"

    def __init__(self, assistant: str, key: str | None, connector: bool, connector_url: str | None = None):
        self.assistant, self.key, self.connector, self.connector_url = assistant, key, connector, connector_url
        self.info = {"target": "external", "assistant": assistant, "connector": connector,
                     "connector_url": connector_url, "wired": False}

    @property
    def available(self) -> bool:
        return bool(self.key) and self.info["wired"]

    async def answer(self, item: dict) -> dict:
        raise NotImplementedError("external assistant target is not wired yet (connector work)")
