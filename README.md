# QindaFox Agent

Firefox/QindaFox extension, native messaging bridge, dependency-free Python CLI/MCP server, and a Codex skill. Optional Jev decisions use the credential on qinda without copying it to the laptop.

## Use

```sh
python3 plugins/qindafox-browser/scripts/install.py
python3 plugins/qindafox-browser/scripts/launch.py
# In another terminal:
~/.local/bin/qindafox-agent sessions
~/.local/bin/qindafox-agent tabs
```

The launcher requires Mozilla geckodriver and Firefox/QindaFox. It creates an isolated temporary profile and installs the extension temporarily. For an existing logged-in browser, load `plugins/qindafox-browser/extension/manifest.json` through `about:debugging#/runtime/this-firefox`. Normal Firefox requires Mozilla signing for permanent extension installation; the generated unsigned XPI is a development build.

Invoke `$qindafox-browser` in Codex. The skill is installed under `~/.codex/skills` on both machines. Plugin MCP configuration is in `.mcp.json`; generic MCP clients can launch `python3 /absolute/path/to/plugins/qindafox-browser/scripts/browser.py mcp`. Full operating instructions: [skill](plugins/qindafox-browser/skills/qindafox-browser/SKILL.md), [tools](plugins/qindafox-browser/skills/qindafox-browser/references/operations.md), [setup](plugins/qindafox-browser/skills/qindafox-browser/references/setup.md).

## Design

`agent → stdio MCP / CLI → user-only Unix socket → Firefox native messaging → extension → observed DOM nodes`

The extension supports explicit tab/frame selection, readable page text, forms, open shadow roots, screenshots, history, navigation, bounded waits, and stale/covered-target rejection. Private tabs are excluded. A toolbar button pauses control. References are consumed after actions. Page and model content is data, not executable code. Password/payment/OTP input values are redacted in observations; screenshots and ordinary page text may still contain sensitive material. Native bridge access is available to processes running as the same OS user; this is not a boundary against malicious same-user software.

Jev uses compact viewport observations, speculative operation/target questions in one API request, persistent SSH/HTTPS, and caller-supplied text. Direct actions and already-satisfied goals incur no model calls. Bounded runs stop on scope, confidence, ambiguity, repetition, request, time, and step limits. They verify success locally and report bytes, tokens when available, and latency. No claim of universal speed or reliability is made from fixture tests.

This release uses synthetic DOM actions. Native trusted input, file upload, canvas-only controls, closed shadow roots, browser chrome, and privileged browser pages need another integration. The launcher uses QindaFox's engine directly rather than its native QindaQt window wrapper. The source remains on qinda at `~/git/QindaFoxAgent.git` and `~/work_SPaC3/QindaFoxAgent`.

## Verify

```sh
python3 -m unittest discover -s tests -v
# With an isolated browser already running:
QINDAFOX_TEST_SESSION=SESSION_ID python3 -m unittest discover -s tests -v
# Optional bounded live API checks (uses the qinda key):
QINDAFOX_TEST_SESSION=SESSION_ID QINDAFOX_TEST_JEV=1 python3 -m unittest discover -s tests -v
```

Live tests cover forms, shadow roots, frames, screenshots, navigation, stale refs, overlays, budgets, and Jev loops. The default suite skips live tests without an explicitly selected session.

## Sources

Original implementation using documented [Firefox native messaging](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging), [tab capture](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/captureTab), [geckodriver](https://firefox-source-docs.mozilla.org/testing/geckodriver/Usage.html), and [TypeSafe typed questions](https://docs.typesafe.ai/primitives). The compact indexed-action approach is informed by [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast); no upstream implementation code is vendored. Packaging follows the [OpenAI plugin format](https://developers.openai.com/plugins/build/plugins).
