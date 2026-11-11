# auto-route

Auto-route is a Claude Code plugin that routes each task to the cheapest Claude model that can handle it reliably.

When auto-route is on, the model you selected in `/model` scores each task on four axes: ambiguity, scope, reasoning depth and risk. That score maps to a tier:

| Tier | Model | Worker agent |
|---|---|---|
| 1 | Haiku | `auto-route:light` |
| 2 | Sonnet | `auto-route:standard` |
| 3 | Opus | `auto-route:deep` |
| 4 | Fable | `auto-route:frontier` |

What the model does with that tier:

- **Same as its own tier:** it does the work itself.
- **Higher tier:** it delegates up to the matching worker right away.
- **Lower tier:** it delegates down when the task is big enough to be worth writing a brief for.

Before each hand-off it prints a line explaining the routing:

```
↳ auto-route: 3 → auto-route:light (A0 S1 R0 K0) — tests for 40 trivial functions, fully specified
```

If a worker fails or answers `ESCALATE`, the task is retried once at the next tier up.

## Install

You need Claude Code and `python3` on your `PATH` (the hook is a small Python script).

```
/plugin marketplace add tomaki19/claude-auto-route
/plugin install auto-route@auto-route
```

The same from a shell:

```
claude plugin marketplace add tomaki19/claude-auto-route
claude plugin install auto-route@auto-route
```

Run `/reload-plugins` or start a new session to load the plugin.

## Usage

| Command | Effect |
|---|---|
| `/auto-route on` / `off` | Turn routing on or off for the current session |
| `/auto-route` | Toggle routing |
| `/auto-route status` | Show the current state |
| `/auto-route default on` / `off` | Set whether new sessions start with routing on |

If another plugin also defines `/auto-route`, use the full name `/auto-route:auto-route`.

Auto-route works with every model in `/model`. You can switch models mid-session and routing adapts on the next turn.

## Notes

- Workers start without the conversation's context. The main model writes them a self-contained brief, which is why small tasks are kept in the main session.
- If your account has no Fable access, tier 4 is never reached in practice: Opus does the work itself. Only `auto-route:frontier` needs Fable.
- To tune the thresholds or the routing behaviour, edit `plugins/auto-route/router.md`. To change worker behaviour, edit `plugins/auto-route/agents/*.md`. After either change, bump `version` in `plugins/auto-route/.claude-plugin/plugin.json` so teammates get the update.

## Layout

```
.claude-plugin/marketplace.json        marketplace catalog
plugins/auto-route/
  .claude-plugin/plugin.json           plugin manifest
  router.md                            routing rules injected into the session
  hooks/hooks.json                     UserPromptSubmit + SessionStart hooks
  scripts/auto_route_hook.py           per-session toggle and rule injection
  skills/auto-route/SKILL.md           the /auto-route command
  agents/{light,standard,deep,frontier}.md   tier workers
```
