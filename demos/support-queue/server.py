#!/usr/bin/env python3
import argparse
import http.server
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit
from tickets import TICKETS

ROOT = Path(__file__).resolve().parent
class State:
    lock = threading.Lock()
    saved = []
    metrics = {}
    started = None

def state():
    with State.lock:
        complete = len(State.saved)==len(TICKETS)
        current = None if complete else {k:v for k,v in TICKETS[len(State.saved)].items() if k!='expected'}
        return {'total':len(TICKETS),'saved':State.saved,'current':current,'complete':complete,'metrics':State.metrics,'elapsed':0 if State.started is None else time.monotonic()-State.started}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def json(self,data,status=200):
        body=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if urlsplit(self.path).path=='/state':return self.json(state())
        if urlsplit(self.path).path=='/results':
            s=state()
            if not s['complete']:return self.json({'error':'Queue not finished'},409)
            expected={t['id']:t['expected'] for t in TICKETS}
            s['correct']=sum(all(r[k]==expected[r['id']][k] for k in ('category','urgency','team')) for r in s['saved'])
            s['mismatches']=[{'id':r['id'],'actual':{k:r[k] for k in ('category','urgency','team')},'expected':expected[r['id']]} for r in s['saved'] if any(r[k]!=expected[r['id']][k] for k in ('category','urgency','team'))]
            return self.json(s)
        return super().do_GET()
    def do_POST(self):
        if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}'):
            return self.json({'error':'Origin rejected'},403)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n>20000:raise ValueError('Request too large')
            d=json.loads(self.rfile.read(n))
            with State.lock:
                if self.path=='/metrics':State.metrics=d
                elif self.path=='/start':State.started=State.started or time.monotonic()
                elif self.path=='/save':
                    if len(State.saved)>=len(TICKETS) or d['id']!=TICKETS[len(State.saved)]['id']:raise ValueError('Wrong current ticket or duplicate save')
                    if d['category'] not in ['billing','access','incident','feature','howto'] or d['urgency'] not in ['critical','normal','low'] or d['team'] not in ['accounts','identity','engineering','product','enablement']:raise ValueError('Invalid classification')
                    State.saved.append({k:d[k] for k in ['id','category','urgency','team']})
                else:raise ValueError('Unknown endpoint')
            self.json({'ok':True})
        except (ValueError,KeyError) as e:self.json({'error':str(e)},400)
    def log_message(self,*a):pass

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8768);args=p.parse_args()
    print(f'Demo: http://127.0.0.1:{args.port}',flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
