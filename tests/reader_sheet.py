"""Run with Python, Playwright, ReportLab, Pillow and a local Chromium installation."""
import base64
import io
import os
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from PIL import Image
from playwright.sync_api import sync_playwright
from reportlab.pdfgen.canvas import Canvas


def two_slides():
    stream = io.BytesIO()
    pdf = Canvas(stream, pagesize=(600, 320))
    for title in ("Folie 1", "Folie 2"):
        pdf.drawString(30, 260, title)
        pdf.showPage()
    pdf.save()
    return base64.b64encode(stream.getvalue()).decode()


def check_reader(browser, url):
    page = browser.new_page(viewport={"width": 1000, "height": 960})
    page.goto(url)
    page.evaluate("""async encoded => {
        view = 'skr';
        const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
        await skAdd([new File([bytes], 'Folien.pdf', {type:'application/pdf'})]);
        await skOpen(S.scripts[0].id);
    }""", two_slides())
    page.wait_for_selector(".pg .ink-overlay")
    page.locator('[title="Werkzeuge"]:visible').first.click()
    page.locator('[title="Stift"]:visible').first.click()
    page.locator(".svc").evaluate("body => body.scrollTop = 260")
    page.wait_for_function("document.querySelector('.svc').scrollTop === 260")
    slides = page.locator(".svc .pdf-surface")
    first, second = (slides.nth(i).bounding_box() for i in range(2))
    start_x = first["x"] + first["width"] * .35
    start_y = first["y"] + first["height"] - 22
    end_x, end_y = start_x + 160, second["y"] + 22
    pen = page.context.new_cdp_session(page)

    def pointer(event, x, y):
        pen.send("Input.dispatchMouseEvent", {
            "type": event, "pointerType": "pen", "x": x, "y": y,
            "button": "left", "buttons": int(event != "mouseReleased"), "force": .65,
        })

    def check_ink_on_second_slide():
        # Opening/closing the toolbar changes the viewport. Sample slide-relative pixels.
        top = slides.nth(1).bounding_box()["y"]
        screenshot = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        assert max(screenshot.getpixel((round(end_x - 3), round(top + 18)))) < 160

    pointer("mousePressed", start_x, start_y)
    for step in range(1, 21):
        pointer("mouseMoved", start_x + 160 * step / 20, start_y + (end_y - start_y) * step / 20)
    check_ink_on_second_slide()
    pointer("mouseReleased", end_x, end_y)
    check_ink_on_second_slide()
    stored = "async () => (await storedInk(S.scripts[0].id)).pages[1]"
    stroke, = page.evaluate(stored)
    page.locator('[title="Rückgängig"]:visible').first.click()
    assert page.evaluate(stored) == []
    page.locator('[title="Wiederholen"]:visible').first.click()
    assert page.evaluate(stored) == [stroke]
    page.evaluate("async () => {closeReader(false); await skOpen(S.scripts[0].id)}")
    page.wait_for_selector(".svc .ink-overlay path")
    check_ink_on_second_slide()
    print("Diagonale sichtbar während der Geste, nach Undo/Redo und nach Wiederöffnen.")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    handler = partial(SimpleHTTPRequestHandler, directory=root)
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as playwright:
            chromium = os.environ.get("CHROMIUM") or shutil.which("chromium")
            browser = playwright.chromium.launch(executable_path=chromium)
            check_reader(browser, f"http://127.0.0.1:{server.server_port}/")
            browser.close()
        server.shutdown()
