# Support-queue browser demonstration

A synthetic 40-request queue, operated using the installed QindaFox extension and live Jev API. This is a fixed-form demonstration, not a benchmark of arbitrary websites or a measured comparison with human work.

The runner imports the plugin's `Browser`/`Jev` clients. It reads each request from the rendered browser page, obtains category and urgency in one Jev request, maps category to a team locally, selects three observed fields, clicks the observed Save button, and verifies the next saved-count state. It never imports the expected-answer dataset or writes classifications through the application's HTTP endpoint directly. Direct HTTP writes contain timing/metrics only.

The server keeps expected answers out of the browser response until the queue is complete. The final `/results` read independently compares persisted form submissions against those expectations.

## Recorded result

- 40/40 complete records matched category, urgency, and assigned team.
- 160 real form actions and 40 verified saves.
- 40 Jev requests with two semantic questions each.
- 39 records accepted automatically; one single-sign-on case was resolved by the main agent after Jev confidence fell to 0.57.
- First 16 records: 6.03 seconds to their saved receipt.
- Full elapsed run: 146.144 seconds, including the low-confidence pause and runner recovery.
- Recorded usage: 23,287 input tokens across the 39 calls with retained usage. The initial runner did not persist usage for its rejected request, so this is not a complete billing total.

The `artifacts/replay.html` page offers a condensed sampled replay and the full original-timing sampled replay. Condensing replaces the 131.463-second screenshot gap during recovery with a two-second hold; the page explicitly labels that edit. It is not a claim that all 40 tickets completed in the condensed video duration. The first 17 frame times were recovered from screenshot filesystem timestamps after the initial runner exited; later times were logged directly. The raw trace, recovery note, final results, screenshot frames, and rendered videos are retained alongside the page.

The initial local Wayland browser window stopped before the measured run. A visible X11-mode QindaFox engine profile ran the workload. The measured runtime excludes page construction and browser startup, and includes model calls, browser reads/actions, verification, per-ticket capture, and the recovery pause.

## Reproduce

Start a fresh server (state is in memory):

```sh
python3 demos/support-queue/server.py
MOZ_ENABLE_WAYLAND=0 ~/.local/bin/qindafox-agent-launch --url http://127.0.0.1:8768
~/.local/bin/qindafox-agent sessions
~/.local/bin/qindafox-agent tabs '{"session":"SESSION_ID"}'
python3 demos/support-queue/run_demo.py --session SESSION_ID --tab TAB_ID
```

Running it again overwrites the generated evidence in `artifacts`; preserve any run you want to keep first. A low-confidence response stops the runner. Inspect the current request and `pending.json`; resume with an explicit agent-reviewed category/urgency using `--resume --resolve-current '{"category":"access","urgency":"normal"}'`. Do not lower thresholds simply to force completion. The published record describes the actual first-run interruption, including its incomplete rejected-request usage.

The test webpage contains only synthetic data. No customer systems, messages, purchases, or external records are changed.
