"""Agents package - core agent implementations."""

from .registry import AgentRegistry, registry as default_registry
from .base_agent import BaseAgent
from .main.agent import MainAgent
from .researcher.agent import ResearcherAgent
from .coder.agent import CoderAgent
from .strategist.agent import StrategistAgent

__all__ = [
    "AgentRegistry",
    "registry",
    "BaseAgent", 
    "MainAgent",
    "ResearcherAgent",
    "CoderAgent",
    "StrategistAgent"
]
