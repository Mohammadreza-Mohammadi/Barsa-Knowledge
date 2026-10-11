"""Barsa Kanban — the agent protocol for building things inside Barsa.

Same shape as the BarsaAgent workflow: a task walks a state machine from a raw
human request to a finished change, four roles write artifacts, and two human
gates stand in the way of anything irreversible.

What differs is what "implementation" means. There is no code to compile here:
a task's output is an `AiChangeBatch` -- the semantic write document Barsa
accepts -- and verification is the contract linter, selector resolution and the
Unknown-guard, not build/lint/test.

The manager speaks `barsa-agent-manager` contract v1, so the existing
BarsaAgent console can drive it unchanged.
"""

MANAGER_CONTRACT_NAME = "barsa-agent-manager"
MANAGER_CONTRACT_VERSION = 1
MANAGER_VERSION = "1.0.0"
PROTOCOL_VERSION = "1"
