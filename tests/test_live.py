"""Integration against an already running isolated Firefox with the add-on loaded.

QINDAFOX_TEST_SESSION=<id> python3 -m unittest discover -s tests -p test_live.py -v
Set QINDAFOX_TEST_JEV=1 to additionally make bounded paid Jev API calls.
"""
import http.server
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins/qindafox-browser/scripts'))
from browser import Browser

HTML = b'''<!doctype html><meta charset="utf-8"><title>QindaFox Agent Fixture</title>
<style>body{font:18px sans-serif;margin:30px}button,input,select{margin:8px;padding:10px}#cover{position:fixed;inset:0;background:#999;z-index:100;display:none}</style>
<h1>Browser integration test</h1>
<label>Name<input id="name" placeholder="Your name"></label>
<label>Password<input id="password" type="password" value="redact-me-789"></label>
<label>Plan<select id="plan"><option value="basic">Basic</option><option value="pro">Pro</option></select></label>
<label><input id="check" type="checkbox">Enable feature</label>
<button id="save" onclick="document.getElementById('result').textContent='Saved '+document.getElementById('name').value">Save draft</button>
<button id="mutate" onclick="document.getElementById('save').textContent='Publish now'">Change label</button>
<button id="coverButton" onclick="document.getElementById('cover').style.display='block'">Cover page</button>
<a href="/done">Open results</a><div id="result" role="status"></div>
<div id="shadow"></div><iframe src="/frame" title="Child frame"></iframe><div id="cover">Overlay</div>
<script>const b=document.createElement('button');b.textContent='Shadow action';b.onclick=()=>b.textContent='Shadow done';document.getElementById('shadow').attachShadow({mode:'open'}).append(b);</script>'''


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<h1>Results complete</h1>' if self.path=='/done' else b'<button onclick="this.textContent=\'Frame done\'">Frame action</button>' if self.path=='/frame' else HTML
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self,*args):
        pass


@unittest.skipUnless(os.environ.get('QINDAFOX_TEST_SESSION'),'requires an isolated live session')
class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.browser = Browser()
        cls.session = os.environ['QINDAFOX_TEST_SESSION']

    @classmethod
    def tearDownClass(cls):
        cls.browser.jev.close()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.tab = self.browser.call('open',{'session':self.session,'url':self.url})['id']
        self.call('wait',text='Browser integration test')

    def tearDown(self):
        self.call('close')

    def call(self,method,**params):
        return self.browser.call(method,{'session':self.session,'tabId':self.tab,**params})

    def find(self,name,**params):
        page = self.call('observe',**params)
        return next(e for e in page['elements'] if e['name']==name)

    def test_forms_shadow_frames_and_screenshot(self):
        page = self.call('observe')
        self.assertNotIn('redact-me-789',json.dumps(page))
        self.call('act',action='fill',ref=self.find('Name')['ref'],text='Ada')
        self.assertEqual(self.find('Name')['value'],'Ada')
        self.call('act',action='select',ref=self.find('Plan')['ref'],value='pro')
        self.assertEqual(self.find('Plan')['value'],'pro')
        self.call('act',action='check',ref=self.find('Enable feature')['ref'],checked=True)
        self.assertTrue(self.find('Enable feature')['checked'])
        self.call('act',action='click',ref=self.find('Save draft')['ref'])
        self.assertTrue(self.call('wait',text='Saved Ada')['matched'])
        self.call('act',action='click',ref=self.find('Shadow action')['ref'])
        self.assertIn('Shadow done',self.call('extract')['text'])
        frames = self.call('frames')
        frame = next(f['frameId'] for f in frames if f['frameId'] != 0)
        self.call('act',action='click',ref=self.find('Frame action',frameId=frame)['ref'],frameId=frame)
        self.assertIn('Frame done',self.call('extract',frameId=frame)['text'])
        self.assertTrue(self.call('screenshot')['dataUrl'].startswith('data:image/jpeg;base64,'))

    def test_old_reference_and_overlay_rejected(self):
        page = self.call('observe')
        save = next(e for e in page['elements'] if e['name']=='Save draft')
        mutate = next(e for e in page['elements'] if e['name']=='Change label')
        self.call('act',action='click',ref=mutate['ref'])
        with self.assertRaisesRegex(RuntimeError,'STALE_REFERENCE'):
            self.call('act',action='click',ref=save['ref'])
        self.call('act',action='click',ref=self.find('Cover page')['ref'])
        ref = self.find('Publish now')['ref']
        with self.assertRaisesRegex(RuntimeError,'OCCLUDED'):
            self.call('act',action='click',ref=ref)

    def test_navigation_wait_and_budget_without_model(self):
        result = self.call('run',goal='Read the heading',allowedOrigins=[self.url],successText='Browser integration test')
        self.assertEqual(result['status'],'verified')
        self.assertEqual(result['requestBytes'],0)
        result = self.call('run',goal='Open results',allowedOrigins=['https://wrong.example'],successText='Results complete')
        self.assertEqual(result['status'],'origin_boundary')
        result = self.call('run',goal='Open results',allowedOrigins=[self.url],successText='Results complete',maxRequestBytes=1000)
        self.assertEqual(result['status'],'request_budget')
        self.call('act',action='click',ref=self.find('Open results')['ref'])
        self.call('wait',urlIncludes='/done',text='Results complete')

    @unittest.skipUnless(os.environ.get('QINDAFOX_TEST_JEV'),'paid Jev test explicitly enabled')
    def test_jev_bounded_loop(self):
        result = self.call('run',goal='Click Open results and stop when Results complete is visible.',allowedOrigins=[self.url],allowedClickNames=['Open results'],successText='Results complete',maxSteps=3)
        print('JEV_RESULT '+json.dumps(result),flush=True)
        self.assertEqual(result['status'],'verified')

    @unittest.skipUnless(os.environ.get('QINDAFOX_TEST_JEV'),'paid Jev test explicitly enabled')
    def test_jev_form_loop(self):
        result = self.call('run',goal='Fill Name with Ada, then click Save draft. Stop when Saved Ada appears.',allowedOrigins=[self.url],allowedClickNames=['Save draft'],values={'Name':'Ada'},successText='Saved Ada',maxSteps=4)
        print('JEV_FORM_RESULT '+json.dumps(result),flush=True)
        self.assertEqual(result['status'],'verified')


if __name__=='__main__':
    unittest.main()
