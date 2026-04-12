#!/usr/bin/env python3
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import requests


DEFAULT_HOST = os.getenv("FIRECRAWL_COMPAT_HOST", "127.0.0.1").strip()
DEFAULT_PORT = int(os.getenv("FIRECRAWL_COMPAT_PORT", "3002"))
DEFAULT_PLAYWRIGHT_URL = os.getenv("FIRECRAWL_PLAYWRIGHT_URL", "http://127.0.0.1:3003/scrape").strip()


class ThreadingCompatHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class FirecrawlCompatService:
    def __init__(self, playwright_url):
        self.playwright_url = str(playwright_url or "").strip()
        self.session = requests.Session()

    def health(self):
        try:
            resp = self.session.get(self.playwright_url.replace("/scrape", "/health"), timeout=15)
            body = resp.json()
        except Exception as exc:
            return {
                "ok": False,
                "service": "firecrawl-compat-bridge",
                "playwright_url": self.playwright_url,
                "playwright_healthy": False,
                "error": str(exc),
            }
        return {
            "ok": True,
            "service": "firecrawl-compat-bridge",
            "playwright_url": self.playwright_url,
            "playwright_healthy": resp.ok,
            "playwright_status": body,
        }

    def scrape(self, payload):
        url = str(payload.get("url") or "").strip()
        if not url:
            raise ValueError("url is required")
        headers = payload.get("headers")
        if not isinstance(headers, dict):
            headers = None
        wait_for = payload.get("waitFor")
        timeout = payload.get("timeout")
        check_selector = payload.get("check_selector") or payload.get("checkSelector")
        upstream_payload = {
            "url": url,
            "wait_after_load": int(wait_for) if wait_for is not None else 1500,
            "timeout": int(timeout) if timeout is not None else 45000,
            "headers": headers,
            "check_selector": check_selector,
        }
        resp = self.session.post(self.playwright_url, json=upstream_payload, timeout=90)
        resp.raise_for_status()
        body = resp.json()
        html = str(body.get("content") or "")
        return {
            "success": True,
            "data": {
                "rawHtml": html,
                "html": html,
                "metadata": {
                    "source": "firecrawl-playwright-compat",
                    "pageStatusCode": body.get("pageStatusCode"),
                    "contentType": body.get("contentType"),
                    "pageError": body.get("pageError"),
                },
            },
        }


class FirecrawlCompatHandler(BaseHTTPRequestHandler):
    service = None

    def _send(self, code, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_GET(self):
        if self.path == "/health":
            status = self.service.health()
            self._send(200 if status.get("ok") else 503, status)
            return
        self._send(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        if self.path != "/v2/scrape":
            self._send(404, {"ok": False, "error": "Not found"})
            return
        try:
            payload = self._read_json()
            result = self.service.scrape(payload)
        except ValueError as exc:
            self._send(400, {"success": False, "error": str(exc)})
            return
        except Exception as exc:
            self._send(502, {"success": False, "error": str(exc)})
            return
        self._send(200, result)


def main():
    parser = argparse.ArgumentParser(description="Firecrawl-compatible scrape bridge backed by Playwright service")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--playwright-url", default=DEFAULT_PLAYWRIGHT_URL)
    args = parser.parse_args()

    FirecrawlCompatHandler.service = FirecrawlCompatService(args.playwright_url)
    server = ThreadingCompatHTTPServer((args.host, args.port), FirecrawlCompatHandler)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
