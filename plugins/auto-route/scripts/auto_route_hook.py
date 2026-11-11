#!/usr/bin/env python3
"""Auto-route mode hook: per-session toggle and injection of the routing rules.

UserPromptSubmit: handles `/auto-route [on|off|status|default on|default off]`, and adds
the routing rules to the context while Auto-route is active (the full rules once, then a
short reminder).
SessionStart (compact/resume): adds the full rules again if the session is active.
"""
import json
import os
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".claude" / "auto-route")
STATE = DATA / "state"
DEFAULT = DATA / "default"  # contains "on" to activate Auto-route in new sessions
RULES = PLUGIN / "router.md"
REMINDER = "Auto-route mode is active: apply the auto-route rules given earlier in this session."
CMD = re.compile(r"^\s*/(?:auto-route:)?auto-route\b\s*(.*)$", re.IGNORECASE)


def default_on():
    return DEFAULT.is_file() and DEFAULT.read_text().strip() == "on"


def load(session):
    try:
        return json.loads((STATE / f"{session}.json").read_text())
    except (OSError, ValueError):
        return {"active": default_on(), "injected": False}


def save(session, state):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / f"{session}.json").write_text(json.dumps(state))


def emit(event, text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def handle_command(args, state):
    words = args.lower().split()
    if words[:1] == ["default"] and words[1:2] in (["on"], ["off"]):
        DATA.mkdir(parents=True, exist_ok=True)
        DEFAULT.write_text(words[1])
        return f"Auto-route default for new sessions set to {words[1]}."
    if words in ([], ["toggle"]):
        state["active"] = not state["active"]
    elif words == ["on"]:
        state["active"] = True
    elif words == ["off"]:
        state["active"] = False
    elif words != ["status"]:
        return "Unknown /auto-route argument. Use: on | off | status | default on | default off."
    if state["active"] and not state["injected"]:
        state["injected"] = True
        return "Auto-route mode is now ON for this session.\n\n" + RULES.read_text()
    if not state["active"]:
        return "Auto-route mode is OFF for this session. Ignore earlier auto-route rules and work normally."
    return "Auto-route mode is ON for this session."


def main():
    data = json.load(sys.stdin)
    event = data.get("hook_event_name")
    session = data.get("session_id")
    if not session:
        return
    state = load(session)

    if event == "UserPromptSubmit":
        match = CMD.match(data.get("prompt", ""))
        if match:
            text = handle_command(match.group(1), state)
        elif not state["active"]:
            text = None
        elif not state["injected"]:
            state["injected"] = True
            text = RULES.read_text()
        else:
            text = REMINDER
        save(session, state)
        if text:
            emit(event, text)
    elif event == "SessionStart" and state["active"]:
        state["injected"] = True
        save(session, state)
        emit(event, RULES.read_text())


if __name__ == "__main__":
    main()
