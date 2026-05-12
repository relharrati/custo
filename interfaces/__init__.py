"""Interfaces package - user-facing components."""

from .terminal import cli as terminal_cli
from .web import backend as web_backend

__all__ = ["terminal_cli", "web_backend"]
