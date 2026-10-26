#!/usr/bin/env python3
"""Local browser demo for the cobol2py translator (localhost only)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "web" / "index.html"
MAX_BODY = 1_000_000


class Handler(BaseHTTPRequestHandler):
    server_version = "cobol2py-demo/1.0"

    def send_bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(status, "application/json; charset=utf-8", body)

    def do_GET(self) -> None:
        if urlparse(self.path).path not in ("/", "/index.html"):
            self.send_error(404)
            return
        try:
            self.send_bytes(200, "text/html; charset=utf-8", PAGE.read_bytes())
        except OSError:
            self.send_error(500, "Demo HTML not found")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/translate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Content-Length inválido."})
            return
        if length < 1 or length > MAX_BODY:
            self.send_json(413, {"error": "El código debe ocupar menos de 1 MB."})
            return
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "La petición no contiene JSON válido."})
            return
        source = data.get("source", "")
        source_format = data.get("format", "auto")
        if not isinstance(source, str) or not source.strip():
            self.send_json(400, {"error": "Pega un programa COBOL antes de traducir."})
            return
        if source_format not in ("auto", "fixed", "free"):
            self.send_json(400, {"error": "Formato no válido."})
            return
        try:
            with tempfile.TemporaryDirectory(prefix="cobol2py-web-") as tmp:
                input_path = Path(tmp) / "pasted_program.cbl"
                input_path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(ROOT / "cobol2py.py"), str(input_path),
                     "--format", source_format],
                    cwd=ROOT, text=True, encoding="utf-8",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=20, check=False,
                )
        except subprocess.TimeoutExpired:
            self.send_json(504, {"error": "La traducción superó el límite de 20 segundos."})
            return
        except OSError as exc:
            self.send_json(500, {"error": f"No se pudo iniciar el traductor: {exc}"})
            return
        if result.returncode:
            self.send_json(422, {
                "error": "El traductor devolvió un error.",
                "details": result.stderr[-4000:],
                "output": result.stdout,
            })
            return
        self.send_json(200, {"python": result.stdout, "stderr": result.stderr})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[cobol2py-demo] {fmt % args}", file=sys.stderr)


def main() -> None:
    host, port = "127.0.0.1", 8765
    print(f"cobol2py demo: http://{host}:{port} (solo accesible desde este equipo)")
    print("Pulsa Ctrl+C para detenerlo.")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
