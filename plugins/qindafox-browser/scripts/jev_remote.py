#!/usr/bin/env python3
"""Run on qinda. JSON-lines protocol; key stays here, HTTPS connection is reused."""
import http.client
import json
import re
import shlex
import sys
import time
from pathlib import Path


def main():
    text = (Path.home() / 'Adulting/api-keys.env').read_text()
    match = re.search(r'^\s*(?:export\s+)?JEV_API_KEY\s*=\s*(.*?)\s*$', text, re.M)
    if not match:
        raise RuntimeError('JEV_API_KEY missing in Adulting/api-keys.env')
    key = shlex.split(match.group(1))[0]
    connection = http.client.HTTPSConnection('api.typesafe.ai', timeout=25)
    for line in sys.stdin:
        started = time.perf_counter()
        try:
            if len(line) > 64000:
                raise ValueError('Jev request exceeds 64KB budget')
            payload = json.loads(line)
            if set(payload) - {'model', 'state', 'questions'}:
                raise ValueError('Unsupported Jev fields')
            connection.request('POST', '/v1/systemone', body=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            body = response.read(1024 * 1024)
            if response.status != 200:
                result = {'error': f'Jev HTTP {response.status}'}
            else:
                result = {'response': json.loads(body), 'apiMs': round((time.perf_counter() - started) * 1000, 1)}
        except Exception as e:
            # Do not return provider bodies or exception text that could include credentials.
            result = {'error': f'Jev transport failed ({type(e).__name__})'}
            connection.close()
            connection = http.client.HTTPSConnection('api.typesafe.ai', timeout=25)
        print(json.dumps(result), flush=True)
    connection.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': f'Jev setup failed ({type(e).__name__}); check qinda Adulting key file'}), flush=True)
        sys.exit(1)
