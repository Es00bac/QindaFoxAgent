# Tool usage

MCP names have the `browser_` prefix; CLI uses the suffix. All except `sessions` accept `session`. Tab operations require `tabId`; content operations optionally accept `frameId` (default 0).

| Operation | Inputs | Result |
| --- | --- | --- |
| sessions | none | Session IDs, browser versions, pause state |
| tabs | session | Tab IDs, titles, URLs, windows |
| open | url, active? | New tab ID |
| navigate | tabId, url | Updated tab |
| observe | tabId, frameId?, maxElements?, maxText?, viewportOnly? | Text, fresh refs, supported actions, options, truncation |
| act | tabId, frameId?, action, ref; text/value/checked/amount/key as appropriate | Dispatch receipt; verify required |
| extract | tabId, frameId?, maxText? | Readable text and URL |
| wait | tabId, frameId?, text?, urlIncludes?, timeoutMs? | Matched state; both supplied criteria must match |
| screenshot | tabId | MCP image or CLI data URL |
| frames | tabId | Frame IDs and URLs |
| activate, close, back, forward, reload | tabId | Operation receipt |
| suggest | tabId, frameId?, goal, history? | Proposal, confidence, request bytes, usage, latency |
| run | See below | Execution trace and verified/stop status |

## CLI examples

Discover real IDs first; these are illustrative:

```sh
~/.local/bin/qindafox-agent observe '{"session":"1234","tabId":2,"maxElements":80,"maxText":5000}'
~/.local/bin/qindafox-agent act '{"session":"1234","tabId":2,"action":"fill","ref":"OBSERVED_REF","text":"Ada"}'
~/.local/bin/qindafox-agent wait '{"session":"1234","tabId":2,"text":"Saved Ada"}'
```

For dynamic/sensitive text, pass JSON through stdin (`qindafox-agent act -`) using structured subprocess input. Do not interpolate untrusted text into shell commands or place secrets in process arguments. `act` supports `click`, `fill`, `select`, `check`, `scroll`, and synthetic `key`. Scroll may omit ref for the window; an element ref scrolls that element.

## Bounded Jev loop

```json
{
  "session": "1234",
  "tabId": 2,
  "goal": "Fill Name with Ada and save the draft. Stop when Saved Ada appears.",
  "allowedOrigins": ["https://app.example.com"],
  "allowedClickNames": ["Save draft"],
  "values": {"Name": "Ada"},
  "successText": "Saved Ada",
  "maxSteps": 6,
  "maxRequestBytes": 48000,
  "timeoutSeconds": 45
}
```

Click names and value keys are exact accessible names, case sensitive. Duplicate names stop the loop. Values are strings for fill/select (select uses option value), booleans for check. Origins include scheme and host/port, without trailing slash. This checks the current page before decisions and link destinations before clicks; it does not block network requests or prevent server redirects. An origin-changing form redirect stops further automation at the next observation.

`maxSteps` caps model calls (1–12, default 8). Request budgets cap serialized request bytes (default 96KB total, max 256KB; 64KB per request). These are resource bounds, not exact currency limits. Metrics report provider usage when available and milliseconds. Runtime checks a soft deadline (default 60 seconds, max 180) before decisions/actions; an in-flight network call may finish later, but no further action is dispatched then.

`minConfidence` defaults to 0.7. Jev `done` returns `unverified_done` unless the local success condition matched. Other stops: `scope_boundary`, `origin_boundary`, `needs_value`, `ambiguous_target`, `low_confidence`, `no_progress`, `request_budget`, `step_budget`, `time_budget`, `action_uncertain`. Satisfied goals return `verified` with zero requests. No automatic model/action retries occur.

Use distinct success text tied to the actual result; generic words already present elsewhere make weak checks. Assess `verified` against the user's broader task before reporting completion.
