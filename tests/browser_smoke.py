"""End-to-end smoke test for the standalone browser translator.

Requires Playwright and Chromium; the CI browser-smoke job installs both.
The test intentionally exercises the CDN-loaded Pyodide runtime, not just HTML markup.
"""
from __future__ import annotations

import asyncio
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format, *args):
        pass


async def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    errors: list[str] = []
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            await page.goto(f"http://127.0.0.1:{server.server_port}/index.html", wait_until="domcontentloaded")
            await page.locator("#example").click()
            await page.locator("#translate").click()
            await page.get_by_text("Traduciendo en este navegador…").wait_for(timeout=180_000)
            await page.wait_for_function(
                "() => document.querySelector('#output').textContent.includes('print(')",
                timeout=180_000,
            )
            output = await page.locator("#output").inner_text()
            status = await page.locator("#status").inner_text()
            if 'print("HOLA MUNDO")' not in output:
                raise AssertionError(f"Expected translated greeting in output, got:\n{output}")
            if "terminada" not in status.lower():
                raise AssertionError(f"Unexpected translation status: {status}")
            if errors:
                raise AssertionError("Uncaught browser errors: " + "; ".join(errors))
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    asyncio.run(main())
