"""uxprobe: simulated usability testing driven by coding-CLI agents.

Point a coding CLI (claude, codex, gemini, cursor-agent, ...) at a website, hand
it a persona and a task, and get back a logged session: what it tried, what it
expected, what actually happened, where it got stuck and how it felt.

These are simulated participants. Mechanical observations are reliable; feelings
are hypotheses to test with real people.
"""

__version__ = "0.2.0"

from .models import Persona, RunResult, RunSpec, Task  # noqa: F401
from .personas import BUILTIN_PERSONAS, get_persona, list_personas  # noqa: F401

__all__ = [
    "__version__",
    "Persona",
    "Task",
    "RunSpec",
    "RunResult",
    "BUILTIN_PERSONAS",
    "get_persona",
    "list_personas",
]
