#!/usr/bin/env python3
import json
import logging
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import error, request

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    stream=sys.stdout,
)
logger = logging.getLogger("eleven_relay")

RELAY_BIND = os.getenv("RELAY_BIND", "127.0.0.1")
RELAY_PORT = int(os.getenv("RELAY_PORT", "8787"))
RELAY_SHARED_TOKEN = os.getenv("RELAY_SHARED_TOKEN", "")
RELAY_TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "20"))
RELAY_RETRY_COUNT = int(os.getenv("RELAY_RETRY_COUNT", "1"))
RELAY_RETRY_DELAY_MS = int(os.getenv("RELAY_RETRY_DELAY_MS", "1500"))
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_OUTBOUND_URL = os.getenv(
    "ELEVEN_OUTBOUND_URL",
    "https://api.elevenlabs.io/v1/convai/sip-trunk/outbound-call",
)
RETRYABLE_PROVIDER_MESSAGES = {
    "max auth retry attemps reached",
    "max auth retry attempts reached",
}


def fail(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def extract_provider_message(body: bytes) -> str:
    try:
        payload = json.loads((body or b"{}").decode())
    except Exception:
        return ""
    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("error") or ""
        return str(message).strip().lower()
    return ""


def should_retry_http_response(status: int, body: bytes, attempt: int) -> bool:
    if attempt >= RELAY_RETRY_COUNT:
        return False
    if status >= 500:
        return True
    message = extract_provider_message(body)
    return message in RETRYABLE_PROVIDER_MESSAGES


def retry_sleep(attempt: int) -> None:
    delay_ms = RELAY_RETRY_DELAY_MS * max(attempt, 1)
    time.sleep(delay_ms / 1000)


def build_request(payload: dict) -> request.Request:
    return request.Request(
        ELEVEN_OUTBOUND_URL,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY,
        },
    )


class RelayHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            fail(self, 404, {"ok": False, "error": "not_found"})
            return
        fail(
            self,
            200,
            {
                "ok": True,
                "service": "eleven_outbound_relay",
                "upstream": ELEVEN_OUTBOUND_URL,
            },
        )

    def do_POST(self) -> None:
        start = time.monotonic()
        if self.path != "/eleven/outbound-call":
            fail(self, 404, {"ok": False, "error": "not_found"})
            return

        auth = self.headers.get("X-Relay-Token", "")
        if not RELAY_SHARED_TOKEN or auth != RELAY_SHARED_TOKEN:
            logger.warning("Forbidden: invalid X-Relay-Token from %s", self.client_address[0])
            fail(self, 403, {"ok": False, "error": "forbidden"})
            return

        if not ELEVEN_API_KEY:
            logger.error("Missing ELEVEN_API_KEY env var")
            fail(self, 500, {"ok": False, "error": "missing_eleven_api_key"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:
            fail(self, 400, {"ok": False, "error": "invalid_json"})
            return

        logger.info("Relaying to %s (%d bytes)", ELEVEN_OUTBOUND_URL, len(raw))

        for attempt in range(RELAY_RETRY_COUNT + 1):
            req = build_request(payload)
            try:
                with request.urlopen(req, timeout=RELAY_TIMEOUT) as resp:
                    body = resp.read()
                    elapsed_ms = int((time.monotonic() - start) * 1000)
                    if should_retry_http_response(resp.status, body, attempt):
                        logger.warning(
                            "Upstream retryable response %d on attempt %d/%d (%dms): %s",
                            resp.status,
                            attempt + 1,
                            RELAY_RETRY_COUNT + 1,
                            elapsed_ms,
                            extract_provider_message(body)[:200],
                        )
                        retry_sleep(attempt + 1)
                        continue
                    logger.info("Upstream %d (%dms, %d bytes)", resp.status, elapsed_ms, len(body))
                    self.send_response(resp.status)
                    self.send_header(
                        "Content-Type",
                        resp.headers.get("Content-Type", "application/json; charset=utf-8"),
                    )
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            except error.HTTPError as exc:
                body = exc.read() or b""
                elapsed_ms = int((time.monotonic() - start) * 1000)
                if should_retry_http_response(exc.code, body, attempt):
                    logger.warning(
                        "Upstream HTTP retryable %d on attempt %d/%d (%dms): %s",
                        exc.code,
                        attempt + 1,
                        RELAY_RETRY_COUNT + 1,
                        elapsed_ms,
                        extract_provider_message(body)[:200] or body[:200],
                    )
                    retry_sleep(attempt + 1)
                    continue
                logger.warning("Upstream HTTP %d (%dms): %s", exc.code, elapsed_ms, body[:200])
                self.send_response(exc.code)
                self.send_header(
                    "Content-Type",
                    exc.headers.get("Content-Type", "application/json; charset=utf-8"),
                )
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as exc:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                if attempt < RELAY_RETRY_COUNT:
                    logger.warning(
                        "Upstream exception retry on attempt %d/%d (%dms): %s",
                        attempt + 1,
                        RELAY_RETRY_COUNT + 1,
                        elapsed_ms,
                        exc,
                    )
                    retry_sleep(attempt + 1)
                    continue
                logger.error("Upstream failed (%dms): %s", elapsed_ms, exc)
                fail(
                    self,
                    502,
                    {
                        "ok": False,
                        "error": "relay_upstream_failed",
                        "message": str(exc),
                    },
                )
                return

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write((fmt % args) + "\n")
        sys.stdout.flush()


def main() -> None:
    server = HTTPServer((RELAY_BIND, RELAY_PORT), RelayHandler)
    print(
        json.dumps(
            {
                "ok": True,
                "service": "eleven_outbound_relay",
                "bind": RELAY_BIND,
                "port": RELAY_PORT,
                "upstream": ELEVEN_OUTBOUND_URL,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
