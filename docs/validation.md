# Validation — 2026-09-26

Environment: qinda-top, QindaFox Firefox engine 155.0.1, Mozilla geckodriver 0.37.1, isolated headless profile. No everyday browser profile was modified. Jev requests used qinda's remote key helper.

Eight unittest cases passed, including five live browser cases. Coverage: fill/select/check/click, visible-text waits, password-value redaction, open shadow roots, child frames, screenshots, stale reference rejection, covered-target rejection, navigation, zero-call success, origin/request budgets, native message framing, typed target compatibility, MCP handshake/error handling, and two live Jev loops. Three protocol tests also passed on qinda. Codex's actual app server discovered all 17 MCP tools after plugin installation.

Single fixture-run timings (not general benchmarks):

| Task | Model calls | Input tokens | Request bytes | Total elapsed |
| --- | ---: | ---: | ---: | ---: |
| Click Open results and verify result text | 1 | 1,253 | 2,665 | 696.9 ms |
| Fill Name, save draft, verify Saved Ada | 2 | 2,520 | 5,360 | 551.8 ms |

The navigation request included SSH startup (597.0 ms request round trip; 205.7 ms API time). The form loop reused the connection (204.4/156.9 ms round trips; 122.3/153.1 ms API times). No main-agent or second text-model call occurred between form actions. Timings include browser work, local verification, and the loop's short post-action settles, but exclude initial browser startup and fixture setup. Currency costs are not inferred from token counts.

The first form test exposed an unnecessary click proposal on an editable field. The Jev action table now offers fill/select directly for those controls, removing that wasted step. The completed form test passed with fill then click. Another fixture issue (incorrect inline JavaScript quoting) was repaired before the shadow-root test passed.

Skill and plugin validators passed. Firefox web-ext lint passed without errors or warnings after declaring data transmission categories and requiring Firefox 142+. JavaScript syntax and git whitespace checks passed. Tests do not establish production-site reliability or cover trusted input, uploads, browser chrome, closed shadow roots, canvas controls, or permanent signed installation.
