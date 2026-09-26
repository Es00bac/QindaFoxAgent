# Installation and recovery

Source hub: `qinda:~/git/QindaFoxAgent.git`. Checkouts: `~/work_SPaC3/QindaFoxAgent` on qinda and `~/work_space/QindaFoxAgent` on the laptop. Fetch/fast-forward before editing, preserve local work, and push changes to qinda.

From the plugin directory:

```sh
python3 scripts/install.py
```

Installs the native host under `~/.mozilla/native-messaging-hosts`, wrappers in `~/.local/bin`, and a skill link under `~/.codex/skills`. Builds `dist/qindafox-agent.xpi`. Requires Python 3.10+ and Linux Unix sockets; no Python packages are needed.

For an isolated browser with the add-on loaded automatically:

```sh
python3 scripts/launch.py
# Headless tests:
python3 scripts/launch.py --headless
```

Uses installed Mozilla geckodriver (`PATH` or `~/.local/bin/geckodriver`) and `/opt/qindafox/firefox`, otherwise Firefox on PATH. Override with `--binary /path/to/firefox`. The temporary profile and add-on last until Ctrl-C. This uses the QindaFox Firefox engine directly, without the QindaQt native-window wrapper. Everyday cookies/logins are not inherited.

To connect an existing Firefox/QindaFox profile, open `about:debugging#/runtime/this-firefox`, choose **Load Temporary Add-on**, and select this plugin's `extension/manifest.json`. It then appears in `sessions`. Temporary add-ons disappear after Firefox exits. Permanent installation in normal release Firefox requires Mozilla signing; an unsigned XPI alone is not permanent. Do not disable signing or alter the everyday profile to bypass it.

The toolbar ON/OFF badge pauses/resumes commands. If disconnected, check the loaded extension, the native manifest's executable, and readable source scripts. The bridge uses a user-only Unix socket, with no HTTP control listener. The isolated launcher additionally uses a loopback geckodriver listener for its own profile.

On qinda, Jev runs locally. Else the default SSH host is `qinda`, running `python3 work_SPaC3/QindaFoxAgent/plugins/qindafox-browser/scripts/jev_remote.py`. Override with `QINDAFOX_JEV_HOST` (`local` skips SSH). Check SSH and script availability without reading the key into agent output. Missing keys, SSH/API errors, and timeouts allow fallback to direct tools. `QINDAFOX_JEV_MODEL` optionally overrides the model default.

The plugin's `.mcp.json` launches the installed `~/.local/bin/qindafox-agent-mcp` wrapper, which runs `scripts/browser.py mcp`. `~/.local/bin/qindafox-agent-launch` starts the isolated browser from any working directory. In a thread predating installation, use the CLI now and start a new thread to discover the skill/MCP tools. Other MCP clients may launch the Python script over stdio.
