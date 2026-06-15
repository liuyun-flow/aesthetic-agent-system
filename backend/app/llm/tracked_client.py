"""V2.5: transparent telemetry wrapper around an OpenAI-compatible client.

`wrap_client(client, provider)` returns a proxy that behaves exactly like the
real client (everything proxied via __getattr__) but times every
`chat.completions.create` call and records token usage + latency. Zero changes
to the agents — they keep calling `client.chat.completions.create(...)`.
"""

import time
from typing import Any


class _TrackedCompletions:
    def __init__(self, real: Any, provider: str) -> None:
        self._real = real
        self._provider = provider

    def create(self, *args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        resp = self._real.create(*args, **kwargs)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            from app.services.telemetry import record_usage

            record_usage(
                provider=self._provider,
                model=kwargs.get("model"),
                usage=getattr(resp, "usage", None),
                latency_ms=latency_ms,
            )
        except Exception:
            pass  # telemetry must never break a request
        return resp

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


class _TrackedChat:
    def __init__(self, real: Any, provider: str) -> None:
        self._real = real
        self.completions = _TrackedCompletions(real.completions, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


class _TrackedClient:
    def __init__(self, real: Any, provider: str) -> None:
        self._real = real
        self.chat = _TrackedChat(real.chat, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


def wrap_client(client: Any, provider: str) -> Any:
    """Wrap an OpenAI-compatible client so chat completions are telemetered."""
    return _TrackedClient(client, provider)
