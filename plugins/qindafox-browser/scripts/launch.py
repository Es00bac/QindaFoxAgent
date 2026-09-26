#!/usr/bin/env python3
"""Start an isolated Firefox/QindaFox browser with the temporary add-on loaded.

Requires geckodriver on PATH. No changes to your everyday browser profile.
Keep this process running for the browser's lifetime; Ctrl-C closes its session.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def request(base, method, path, data=None):
    req = urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=60) as response:
            result = json.load(response)['value']
    except urllib.error.HTTPError as e:
        result = json.load(e)['value']
        raise RuntimeError(result.get('message','WebDriver error')) from None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--binary',default='/opt/qindafox/firefox' if Path('/opt/qindafox/firefox').exists() else shutil.which('firefox'))
    parser.add_argument('--url',default='about:blank')
    args = parser.parse_args()
    driver = shutil.which('geckodriver') or (str(Path.home()/'.local/bin/geckodriver') if (Path.home()/'.local/bin/geckodriver').exists() else None)
    if not driver or not args.binary:
        parser.error('Install Mozilla geckodriver on PATH and Firefox/QindaFox first')
    xpi = Path(__file__).resolve().parents[1]/'dist/qindafox-agent.xpi'
    if not xpi.exists():
        parser.error('Run scripts/install.py first')
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1',0))
        port = reserve.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    session = None
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen([driver,'--host','127.0.0.1','--port',str(port)],stdout=log,stderr=log)
        try:
            for _ in range(100):
                try:
                    request(base,'GET','/status')
                    break
                except (OSError,RuntimeError):
                    if proc.poll() is not None:
                        raise RuntimeError('geckodriver exited at startup')
                    time.sleep(.05)
            result = request(base,'POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'firefox','moz:firefoxOptions':{'binary':args.binary,'args':['-headless'] if args.headless else [],'prefs':{'browser.shell.checkDefaultBrowser':False}}}}})
            session = result['sessionId']
            request(base,'POST',f'/session/{session}/moz/addon/install',{'path':str(xpi),'temporary':True})
            request(base,'POST',f'/session/{session}/url',{'url':args.url})
            print(json.dumps({'status':'ready','browser':'QindaFox/Firefox','profile':'isolated temporary profile','pid':proc.pid}),flush=True)
            while proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if session:
                try:
                    request(base,'DELETE',f'/session/{session}')
                except Exception:
                    pass
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    main()
