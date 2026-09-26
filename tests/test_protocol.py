import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]/'plugins/qindafox-browser/scripts'
sys.path.insert(0,str(SCRIPTS))
from native_host import read_native, write_native
from browser import suggestion_payload


class ProtocolTests(unittest.TestCase):
    def test_native_frames(self):
        stream = io.BytesIO()
        write_native(stream,{'unicode':'café'})
        stream.seek(0)
        self.assertEqual(read_native(stream),{'unicode':'café'})
        with self.assertRaises(ValueError):
            read_native(io.BytesIO(struct.pack('=I',100000000)))
        with self.assertRaises(EOFError):
            read_native(io.BytesIO(b'\x01\x00'))

    def test_jev_targets_exclude_secrets_and_incompatible_controls(self):
        page = {'title':'test','text':'hello','elements':[
            {'ref':'a','role':'textbox','name':'Password','sensitive':True,'disabled':False,'value':'secret','actions':['fill']},
            {'ref':'b','role':'button','name':'Go','sensitive':False,'disabled':False,'actions':['click']},
            {'ref':'c','role':'textbox','name':'Email','sensitive':False,'disabled':False,'value':'private@example.com','actions':['fill']}
        ]}
        payload, elements = suggestion_payload('Open results',page)
        encoded = json.dumps(payload)
        self.assertNotIn('secret',encoded)
        self.assertNotIn('private@example.com',encoded)
        self.assertEqual(payload['questions']['click_target']['criteria'],{'1':'button: Go'})
        self.assertEqual(payload['questions']['fill_target']['criteria'],{'2':'textbox: Email'})
        self.assertEqual(len(elements),2)

    def test_mcp_handshake_and_errors(self):
        requests = [
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26'}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'not-real'},
            {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'browser_observe','arguments':{'session':'not-a-session','tabId':1}}}
        ]
        proc = subprocess.run([sys.executable,str(SCRIPTS/'browser.py'),'mcp'],input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True,check=True)
        result = [json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual(len(result),4)
        self.assertEqual(result[0]['result']['protocolVersion'],'2025-03-26')
        self.assertIn('browser_run',[t['name'] for t in result[1]['result']['tools']])
        self.assertEqual(result[2]['error']['code'],-32601)
        self.assertTrue(result[3]['result']['isError'])


if __name__ == '__main__':
    unittest.main()
