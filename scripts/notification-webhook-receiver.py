"""Receptor HTTP sintético local para validación manual; no usar en producción."""

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        timestamp = self.headers.get("X-PliegoCheck-Timestamp", "")
        secret = os.environ.get("PLIEGOCHECK_WEBHOOK_RECEIVER_SECRET", "local-fixture-secret")
        expected = (
            "v1="
            + hmac.new(
                secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256
            ).hexdigest()
        )
        valid = hmac.compare_digest(expected, self.headers.get("X-PliegoCheck-Signature", ""))
        self.send_response(204 if valid else 401)
        self.end_headers()
        print(
            json.dumps(
                {
                    "valid_signature": valid,
                    "delivery_id": self.headers.get("X-PliegoCheck-Delivery-Id"),
                    "bytes": len(body),
                }
            ),
            flush=True,
        )

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
