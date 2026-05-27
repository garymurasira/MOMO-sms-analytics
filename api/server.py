"""
MoMo SMS Analytics — REST API Server

Pure standard-library HTTP server exposing CRUD endpoints over transactions.json.
Run with:  python api/server.py  or  python -m api.server
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Optional, Tuple

# ---------- constants ----------
DATA_FILE = Path(__file__).parent / "data" / "transactions.json"
HOST = "localhost"
PORT = 8000


# ---------- store ----------


class TransactionStore:
    """In-memory store backed by transactions.json.

    Loads all records at startup and maintains an id→index map for O(1)
    lookups — a clean hook for Merci's DSA optimisation work later.
    """

    def __init__(self, filepath: Path = DATA_FILE) -> None:
        """Load transactions from *filepath* and build the lookup index."""
        with open(filepath, "r", encoding="utf-8") as fh:
            self._records: list[dict[str, Any]] = json.load(fh)

        self._index: dict[int, int] = {
            record["id"]: idx for idx, record in enumerate(self._records)
        }
        self._next_id: int = (max(self._index.keys()) + 1) if self._index else 1

    def list_all(self) -> list[dict[str, Any]]:
        """Return a copy of all transactions."""
        return list(self._records)

    def get(self, id: int) -> Optional[dict[str, Any]]:
        """Return the transaction with the given *id*, or None if not found."""
        idx = self._index.get(id)
        if idx is None:
            return None
        return self._records[idx]

    def add(self, record: dict[str, Any]) -> int:
        """Append *record*, assign a new id, and return that id."""
        new_id = self._next_id
        self._next_id += 1
        record["id"] = new_id
        self._index[new_id] = len(self._records)
        self._records.append(record)
        return new_id

    def update(self, id: int, patch: dict[str, Any]) -> bool:
        """Apply *patch* fields to the transaction with the given *id*.

        Returns True on success, False if the id does not exist.
        The id field in *patch* is ignored to prevent corruption.
        """
        idx = self._index.get(id)
        if idx is None:
            return False
        patch.pop("id", None)
        self._records[idx].update(patch)
        return True

    def delete(self, id: int) -> bool:
        """Remove the transaction with the given *id*.

        Returns True on success, False if the id does not exist.
        Rebuilds the id→index map after deletion.
        """
        idx = self._index.get(id)
        if idx is None:
            return False
        self._records.pop(idx)
        self._index = {
            record["id"]: i for i, record in enumerate(self._records)
        }
        return True


# ---------- handlers ----------

# Module-level store instance — set by run() before the server starts.
_store: Optional[TransactionStore] = None


class TransactionsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MoMo SMS Analytics API.

    Endpoints
    ---------
    GET  /                    → 200 welcome JSON
    GET  /transactions        → 200 array of all records
    GET  /transactions/{id}   → 200 single record | 404
    POST /transactions        → 201 created record | 400 bad body
    PUT  /transactions/{id}   → 200 updated record | 404 | 400 bad body
    DELETE /transactions/{id} → 204 No Content     | 404

    Auth hooks
    ----------
    Each verb method begins with a commented-out auth hook block.
    Gary replaces those two comment lines with a real authenticate() call
    to add Basic Auth without touching anything else.
    """

    # ------------------------------------------------------------------
    # Verb methods
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        # === AUTH HOOK (Gary fills this in) ===
        # if not authenticate(self):
        #     return self._send_unauthorized()
        # =======================================

        resource, resource_id = self._parse_path()
        if resource is None:
            return

        if resource == "":
            self._send_json(200, {"name": "MoMo SMS API", "version": "1.0"})
            return

        if resource == "transactions":
            if resource_id is None:
                self._send_json(200, _store.list_all())
            else:
                record = _store.get(resource_id)
                if record is None:
                    self._send_json(404, {"error": "transaction not found"})
                else:
                    self._send_json(200, record)
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        # === AUTH HOOK (Gary fills this in) ===
        # if not authenticate(self):
        #     return self._send_unauthorized()
        # =======================================

        resource, resource_id = self._parse_path()
        if resource is None:
            return

        if resource == "transactions" and resource_id is None:
            data, err = self._read_json_body()
            if err:
                self._send_json(400, {"error": err})
                return
            new_id = _store.add(data)
            self._send_json(201, _store.get(new_id))
            return

        self._send_json(404, {"error": "not found"})

    def do_PUT(self) -> None:
        # === AUTH HOOK (Gary fills this in) ===
        # if not authenticate(self):
        #     return self._send_unauthorized()
        # =======================================

        resource, resource_id = self._parse_path()
        if resource is None:
            return

        if resource == "transactions" and resource_id is not None:
            data, err = self._read_json_body()
            if err:
                self._send_json(400, {"error": err})
                return
            if not _store.update(resource_id, data):
                self._send_json(404, {"error": "transaction not found"})
            else:
                self._send_json(200, _store.get(resource_id))
            return

        self._send_json(404, {"error": "not found"})

    def do_DELETE(self) -> None:
        # === AUTH HOOK (Gary fills this in) ===
        # if not authenticate(self):
        #     return self._send_unauthorized()
        # =======================================

        resource, resource_id = self._parse_path()
        if resource is None:
            return

        if resource == "transactions" and resource_id is not None:
            if not _store.delete(resource_id):
                self._send_json(404, {"error": "transaction not found"})
            else:
                self.send_response(204)
                self.end_headers()
            return

        self._send_json(404, {"error": "not found"})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _send_json(self, status_code: int, payload: Any) -> None:
        """Serialize *payload* to JSON and send a complete HTTP response."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Tuple[Optional[dict], Optional[str]]:
        """Read the request body and parse it as JSON.

        Returns (data, None) on success or (None, error_message) on failure.
        """
        length_header = self.headers.get("Content-Length")
        if not length_header:
            return None, "missing Content-Length header"
        try:
            length = int(length_header)
        except ValueError:
            return None, "invalid Content-Length"
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8")), None
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return None, f"invalid JSON: {exc}"

    def _parse_path(self) -> Tuple[Optional[str], Optional[int]]:
        """Parse the request path into (resource, id_or_None).

        Valid shapes
        ------------
        /                    → ("", None)
        /transactions        → ("transactions", None)
        /transactions/{id}   → ("transactions", int_id)

        Any other shape sends a 404 and returns (None, None) so the caller
        can return immediately without writing a second response.
        """
        path = self.path.split("?")[0].rstrip("/")
        parts = [p for p in path.split("/") if p]

        if len(parts) == 0:
            return "", None

        if len(parts) == 1:
            return parts[0], None

        if len(parts) == 2:
            try:
                resource_id = int(parts[1])
            except ValueError:
                self._send_json(400, {"error": "id must be an integer"})
                return None, None
            return parts[0], resource_id

        self._send_json(404, {"error": "not found"})
        return None, None

    def _send_unauthorized(self) -> None:
        """Send a 401 response with the WWW-Authenticate header.

        Gary wires in his authenticate() function at the top of each verb
        method; this method handles the response so his hook is one line.
        """
        body = json.dumps({"error": "unauthorized"}).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress per-request log lines; only run() prints to stdout."""


# ---------- bootstrap ----------


def run() -> None:
    """Load the store and start the HTTP server on HOST:PORT."""
    global _store
    _store = TransactionStore()
    server = HTTPServer((HOST, PORT), TransactionsHandler)
    print(f"Server listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    run()
