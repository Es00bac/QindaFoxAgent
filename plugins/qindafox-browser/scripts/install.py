#!/usr/bin/env python3
"""Install the native host and discoverable skill; build the Firefox XPI."""
import json
import os
from pathlib import Path
import shlex
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    home = Path.home()
    bindir = home / '.local/bin'
    bindir.mkdir(parents=True,exist_ok=True)
    for name,script,args in [('qindafox-agent-host','native_host.py',''),('qindafox-agent','browser.py',''),('qindafox-agent-mcp','browser.py','mcp')]:
        path = bindir / name
        path.write_text('#!/bin/sh\nexec python3 ' + shlex.quote(str(root / 'scripts' / script)) + (' '+args if args else '') + ' "$@"\n')
        path.chmod(0o700)
    native = home / '.mozilla/native-messaging-hosts'
    native.mkdir(parents=True,exist_ok=True)
    (native / 'org.qindafox.agent.json').write_text(json.dumps({'name':'org.qindafox.agent','description':'Local QindaFox Agent bridge','path':str(bindir/'qindafox-agent-host'),'type':'stdio','allowed_extensions':['agent@qindafox.local']},indent=2)+'\n')
    skill_home = Path(os.environ.get('CODEX_HOME',str(home/'.codex'))) / 'skills'
    skill_home.mkdir(parents=True,exist_ok=True)
    destination = skill_home / 'qindafox-browser'
    source = root/'skills/qindafox-browser'
    if destination.is_symlink() and destination.resolve() == source:
        pass
    elif destination.exists() or destination.is_symlink():
        raise RuntimeError(f'Existing unrelated skill at {destination}; preserved')
    else:
        destination.symlink_to(source,target_is_directory=True)
    dist = root/'dist'
    dist.mkdir(exist_ok=True)
    xpi = dist/'qindafox-agent.xpi'
    with zipfile.ZipFile(xpi,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((root/'extension').rglob('*')):
            if path.is_file():
                archive.write(path,path.relative_to(root/'extension'))
    print(json.dumps({'nativeHost':'installed','skill':str(destination),'extension':str(xpi),'next':'Load extension/manifest.json in about:debugging#/runtime/this-firefox, or run scripts/launch.py for an isolated agent browser.'},indent=2))


if __name__ == '__main__':
    main()
