"""Built-in vs custom tool-selection framework.

Maps a task description to the correct tool. Built-in tools (Grep, Glob, Read, Write, Edit,
Bash) handle codebase/file work; the custom inventory MCP tools handle domain operations. The
framework also encodes the Edit-fails fallback: when Edit cannot find a unique anchor, the
reliable choice is Read + Write.
"""

from __future__ import annotations

CUSTOM_INVENTORY = "<custom inventory tool>"

# Priority-ordered: the first matching rule wins, so rules run from most specific to most general.
# 1) The Edit-fails fallback is a special case of Edit, so it is checked before Edit itself.
# 2) Domain operations always route to the custom inventory tools, never a built-in.
# 3) The file/codebase built-ins follow, each keyed on distinctive verbs so a "search" task lands
#    on Grep while a "matching pattern" task lands on Glob.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    # Edit could not find a unique anchor -> fall back to Read + Write.
    ("Read+Write", ("not unique", "anchor", "edit failed", "edit fails", "no unique anchor")),
    # Domain operations -> custom inventory tools.
    (
        CUSTOM_INVENTORY,
        (
            "stock", "inventory", "restock", "units", "sku",
            "return", "refund",
            "price", "markdown",
            "shrinkage", "theft", "warehouse",
        ),
    ),
    # File/codebase built-ins.
    ("Glob", ("glob", "matching", "every file", "*.", "**/")),
    ("Grep", ("grep", "search", "callers", "occurrences", "references", "usages")),
    ("Bash", ("bash", "shell", "run the", "run command", "run script", "terminal", "command line")),
    ("Write", ("create", "new file", "from scratch", "generate a new", "write a new")),
    ("Edit", ("edit", "in-place", "modify the", "replace the", "change the line")),
    ("Read", ("read", "contents", "view", "open the file", "show the file", "cat ")),
]


def select_tool(task: str) -> str:
    """Return the tool best suited to ``task``.

    Returns a built-in tool name (``Grep``/``Glob``/``Read``/``Write``/``Edit``/``Bash``),
    the ``Read+Write`` fallback, or :data:`CUSTOM_INVENTORY` for domain operations.
    """
    text = task.lower()
    for tool, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return tool
    # No rule matched: default to the most read-only, least destructive tool.
    return "Read"

