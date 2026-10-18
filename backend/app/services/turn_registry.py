"""
Which conversations have a chat turn running right now.

WHY: a turn outlives the socket that started it. A client that reloads the
page mid-turn (a phone browser does that on its own when the tab was in the
background) loads the conversation, finds its own question and nothing after
it, and has no way to tell "the answer is still coming" from "nothing is
coming". This registry is that way: the conversation endpoint reports it as
``turn_in_progress`` and the client waits and polls instead of giving up.

In-process on purpose: the API runs as ONE uvicorn worker (see Dockerfile),
so a set is both correct and free. A second worker would need this in Redis.
"""

from __future__ import annotations

_running: set[str] = set()


def turn_started(conversation_id: str) -> None:
    """Record that a turn is now running for ``conversation_id``."""
    _running.add(conversation_id)


def turn_finished(conversation_id: str) -> None:
    """Record that the turn for ``conversation_id`` ended, however it ended."""
    _running.discard(conversation_id)


def turn_in_progress(conversation_id: str) -> bool:
    """True while a turn for ``conversation_id`` is running."""
    return conversation_id in _running
