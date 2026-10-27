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
    dialog_messages: list[str] = []

    async def capture_dialog(dialog):
        dialog_messages.append(dialog.message)
        await dialog.accept()

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("dialog", capture_dialog)
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
            if "str(mensaje)" not in output or 'str("GRANDE")' not in output:
                raise AssertionError(f"Expected translated variable and branch in output, got:\n{output}")
            if "terminada" not in status.lower():
                raise AssertionError(f"Unexpected translation status: {status}")
            if errors:
                raise AssertionError("Uncaught browser errors: " + "; ".join(errors))

            # Exercise the standalone agent UI with synthetic files; source text stays in-browser.
            await page.goto(f"http://127.0.0.1:{server.server_port}/agent.html", wait_until="domcontentloaded")
            await page.locator("#files").set_input_files([
                {
                    "name": "MAIN.cbl",
                    "mimeType": "text/plain",
                    "buffer": b'IDENTIFICATION DIVISION.\\nPROGRAM-ID. MAIN.\\nPROCEDURE DIVISION.\\n CALL "SUBPROG".\\n CALL "MISSING".\\n STOP RUN.\\n',
                },
                {
                    "name": "SUBPROG.cbl",
                    "mimeType": "text/plain",
                    "buffer": b"IDENTIFICATION DIVISION.\\nPROGRAM-ID. SUBPROG.\\nPROCEDURE DIVISION.\\n GOBACK.\\n",
                },
            ])
            await page.locator("#analyze").click()
            try:
                await page.locator("#results").wait_for(state="visible", timeout=5000)
            except Exception as error:
                raise AssertionError(
                    "Agent analysis failed; dialogs=" + repr(dialog_messages)
                    + "; browser errors=" + repr(errors)
                ) from error
            stats = await page.locator("#stats").inner_text()
            unresolved = await page.locator("#unresolved").inner_text()
            if "2" not in stats or "MISSING" not in unresolved:
                raise AssertionError("Agent inventory missed expected files/reference: " + stats + " / " + unresolved)
            async with page.expect_download() as download_info:
                await page.locator("#json").click()
            download = await download_info.value
            if download.suggested_filename != "cobol2py-browser-inventory.json":
                raise AssertionError("Unexpected agent export name: " + download.suggested_filename)
            if errors:
                raise AssertionError("Uncaught browser errors: " + "; ".join(errors))
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    asyncio.run(main())
