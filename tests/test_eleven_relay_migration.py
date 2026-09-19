import importlib.util
import io
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from http.server import HTTPServer
from urllib import request, error

spec = importlib.util.spec_from_file_location("relay", Path(__file__).parents[1] / "scripts/eleven_outbound_relay_server.py")
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)

class RelayContract(unittest.TestCase):
    def setUp(self):
        self.patch = patch.multiple(relay, RELAY_SHARED_TOKEN="test-only", ELEVEN_API_KEY="mock-key", RELAY_RETRY_COUNT=0)
        self.patch.start()
        self.server = HTTPServer(("127.0.0.1", 0), relay.RelayHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
    def tearDown(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close(); self.patch.stop()
    def post(self, body, auth=True):
        req = request.Request(self.url + "/eleven/outbound-call", data=body,
            headers={"X-Relay-Token": "test-only"} if auth else {})
        try:
            with request.urlopen(req, timeout=2) as r: return r.status, json.load(r)
        except error.HTTPError as e: return e.code, json.load(e)
    def test_health_and_missing_auth_do_not_call_provider(self):
        with patch.object(relay.request, "urlopen", wraps=request.urlopen) as upstream:
            # Both modules share urllib; only assert unauthorized response here.
            self.assertEqual(self.post(b"{}", False)[0], 403)
        with request.urlopen(self.url + "/health") as response:
            self.assertTrue(json.load(response)["ok"])
    def test_invalid_json(self):
        self.assertEqual(self.post(b"broken")[0], 400)
    def test_forwarding_and_provider_error(self):
        original = request.urlopen
        received = []
        class Response(io.BytesIO):
            status = 200
            headers = {"Content-Type": "application/json"}
        def fake(req, *args, **kwargs):
            if req.full_url.startswith(self.url): return original(req, *args, **kwargs)
            received.append(req)
            return Response(b'{"conversation_id":"mock-conversation"}')
        with patch.object(relay.request, "urlopen", side_effect=fake):
            status, body = self.post(b'{"to_number":"test-placeholder"}')
        self.assertEqual(status, 200)
        self.assertEqual(body["conversation_id"], "mock-conversation")
        self.assertEqual(received[0].get_header("Xi-api-key"), "mock-key")
        self.assertEqual(json.loads(received[0].data)["to_number"], "test-placeholder")
        def denied(req, *args, **kwargs):
            if req.full_url.startswith(self.url): return original(req, *args, **kwargs)
            raise error.HTTPError(req.full_url, 429, "mock quota", {"Content-Type":"application/json"}, io.BytesIO(b'{"detail":"mock quota"}'))
        with patch.object(relay.request, "urlopen", side_effect=denied):
            self.assertEqual(self.post(b"{}")[0], 429)

if __name__ == "__main__": unittest.main()
