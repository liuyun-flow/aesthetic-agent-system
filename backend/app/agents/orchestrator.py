"""Orchestrator — coordinates multiple agents for compound workflows."""

from openai import OpenAI

from app.agents.analyzer import AnalyzerAgent
from app.agents.critic import CriticAgent
from app.agents.iterator import IteratorAgent
from app.agents.profile import ProfileAgent


class OrchestratorAgent:
    """Holds references to all agents and exposes convenience compound methods.

    In the MVP this is a thin container; as the system grows the orchestrator
    can chain agents together (e.g. analyze → critique → iterate in one call).
    """

    def __init__(self, client: OpenAI, model: str, reasoning_model: str) -> None:
        self.analyzer = AnalyzerAgent(client=client, model=model)
        self.critic = CriticAgent(client=client, model=model)
        self.iterator = IteratorAgent(client=client, model=model)
        self.profile = ProfileAgent(client=client, model=reasoning_model)
