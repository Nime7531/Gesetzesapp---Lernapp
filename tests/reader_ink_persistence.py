"""Regressionstest: Pencil-Striche dürfen nach dem Absetzen nicht verschwinden.

1. WebKit meldet für ungezeichnete SVG-Formen (fill:none) im IntersectionObserver keine Fläche.
   Der Test bildet das nach und prüft, dass der gerade geschriebene Strich sichtbar bleibt.
2. Ein vom System abgebrochener Stift-Zeiger (pointercancel) darf den Strich nicht verwerfen.
3. Der Wechsel zum Radierer darf das Dokument nicht unter dem Stift verschieben.

Run with Python, Playwright, ReportLab and a local Chromium (env CHROMIUM).
"""
import base64, io, os, shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
from reportlab.pdfgen.canvas import Canvas

WEBKIT_IO = """(() => {
  const Native = window.IntersectionObserver;
  const painted = el => !(el instanceof SVGGeometryElement) || getComputedStyle(el).fill !== 'none' || getComputedStyle(el).stroke !== 'none';
  window.IntersectionObserver = class extends Native {
    constructor(cb, opts) { super(entries => cb(entries.map(e => painted(e.target) ? e :
      ({target: e.target, isIntersecting: false, intersectionRatio: 0, boundingClientRect: new DOMRect(), intersectionRect: new DOMRect(), rootBounds: e.rootBounds, time: e.time})), this), opts); }
  };
})();"""

VISIBLE = "() => document.querySelectorAll('#sv .svc .pg > .ink-overlay:not(.ink-live) path').length"
STORED = "async () => (await storedInk(S.scripts[0].id)).pages[1]?.length || 0"


def pdf():
    s = io.BytesIO(); c = Canvas(s, pagesize=(595, 842))
    for i in range(2): c.drawString(60, 760, f"Seite {i + 1}"); c.showPage()
    c.save(); return base64.b64encode(s.getvalue()).decode()


def open_reader(page, url):
    page.goto(url)
    page.evaluate("""async enc => { view='skr'; const b=Uint8Array.from(atob(enc),c=>c.charCodeAt(0));
        await skAdd([new File([b],'Folien.pdf',{type:'application/pdf'})]); await skOpen(S.scripts[0].id); }""", pdf())
    page.wait_for_selector(".pg .ink-overlay")
    page.locator('[title="Werkzeuge"]:visible').first.click()
    page.locator('[title="Stift"]:visible').first.click()


def pen(page):
    cdp = page.context.new_cdp_session(page)
    def ev(kind, x, y):
        cdp.send("Input.dispatchMouseEvent", {"type": kind, "pointerType": "pen", "x": x, "y": y,
                 "button": "left", "buttons": int(kind != "mouseReleased"), "force": .6})
    return ev


def check_visible_after_lift(browser, url):
    ctx = browser.new_context(viewport={"width": 1000, "height": 900}); ctx.add_init_script(WEBKIT_IO)
    page = ctx.new_page(); open_reader(page, url); ev = pen(page)
    box = page.locator("#sv .pdf-surface").first.bounding_box(); x, y = box["x"] + 120, box["y"] + 160
    ev("mousePressed", x, y)
    for i in range(1, 16): ev("mouseMoved", x + 10 * i, y + 3 * i)
    ev("mouseReleased", x + 150, y + 45)
    page.wait_for_timeout(800)
    assert page.evaluate(STORED) == 1, "Strich wurde nicht gespeichert"
    assert page.evaluate(VISIBLE) >= 1, "Strich verschwindet nach dem Absetzen (WebKit-IntersectionObserver)"
    page.locator("#sv .svc").evaluate("b => b.scrollTop = 4000"); page.wait_for_timeout(500)
    page.locator("#sv .svc").evaluate("b => b.scrollTop = 0"); page.wait_for_timeout(700)
    assert page.evaluate(VISIBLE) >= 1, "Strich fehlt nach Weg- und Zurückscrollen"
    ctx.close()


def check_cancel_keeps_stroke(browser, url):
    ctx = browser.new_context(viewport={"width": 1000, "height": 900}); page = ctx.new_page()
    open_reader(page, url); ev = pen(page)
    page.evaluate("() => document.querySelector('#sv .svc').addEventListener('pointerdown', e => window.__pid = e.pointerId, true)")
    box = page.locator("#sv .pdf-surface").first.bounding_box(); x, y = box["x"] + 120, box["y"] + 300
    ev("mousePressed", x, y)
    for i in range(1, 16): ev("mouseMoved", x + 10 * i, y + 3 * i)
    page.evaluate("""() => { const pg = document.querySelector('#sv .svc .pg');
        pg.dispatchEvent(new PointerEvent('pointercancel', {pointerId: window.__pid, pointerType: 'pen', bubbles: true})) }""")
    ev("mouseReleased", x + 150, y + 45)
    page.wait_for_timeout(600)
    assert page.evaluate(STORED) == 1, "Abgebrochener Stift-Zeiger hat den Strich verworfen"
    assert page.evaluate(VISIBLE) >= 1
    ctx.close()


def check_eraser_keeps_layout(browser, url):
    ctx = browser.new_context(viewport={"width": 1000, "height": 900}); page = ctx.new_page()
    open_reader(page, url)
    top = lambda: page.locator("#sv .pdf-surface").first.bounding_box()["y"]
    before = top()
    eraser = page.locator('#sv .ink-dock [title="Radierer"]')
    if not eraser.is_visible():
        page.locator('#sv .ink-dock .dock-fold').click(); page.wait_for_timeout(300)
    before = top()
    eraser.click(); page.wait_for_timeout(300)
    assert page.locator("#sv .ink-eraser-bar").is_visible(), "Radierer-Optionen nicht sichtbar"
    assert abs(top() - before) < 1, f"Dokument springt beim Radierer um {top() - before:.0f}px"
    ctx.close()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    handler = partial(SimpleHTTPRequestHandler, directory=root)
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get("CHROMIUM") or shutil.which("chromium"))
            url = f"http://127.0.0.1:{server.server_port}/"
            results = []
            for name, fn in (("Sichtbar nach Absetzen (WebKit-IO)", check_visible_after_lift), ("pointercancel behält Strich", check_cancel_keeps_stroke),
                             ("Radierer ohne Layoutsprung", check_eraser_keeps_layout)):
                try: fn(browser, url); results.append(f"OK    {name}")
                except Exception as e: results.append(f"FEHLER {name}: {str(e).splitlines()[0][:160]}")
            browser.close()
        server.shutdown()
    print("\n".join(results))
    raise SystemExit(any(r.startswith("FEHLER") for r in results))
