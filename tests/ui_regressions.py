"""Regressionstests für die Darstellungsschicht (Glas, Symbole, Hintergründe).

1. Glas-Optik: Beim Navigieren zwischen Bereichen dürfen sich keine Brechungsfilter ansammeln (Speicher).
2. Kontrast: „Start“ unter dem Markennamen hat auf der Auswahlplatte mindestens 4,5 : 1 (Dunkel, Navy).
3. Reader: kein Liquid Glass (keine Hintergrundfilter an Leiste, Dock, Gesetzesansicht).

Run with Python, Playwright and a local Chromium (env CHROMIUM).
"""
import os, re, shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

LAW = "\n".join(f"§ {i} Norm {i}\n(1) Text der Norm {i}." for i in range(1, 6))
ADD_LAW = "txt => { const id='l'+uid(); S.laws.push({id,name:'Testgesetz',paras:parse(txt)}); cur=id; view='read'; save(); draw(); }"


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = rgb
    return .2126 * ch(r) + .7152 * ch(g) + .0722 * ch(b)


def check_no_filter_growth(browser, url):
    page = browser.new_page(viewport={"width": 1180, "height": 820})
    page.goto(url); page.wait_for_timeout(1000); page.evaluate(ADD_LAW, LAW)
    counts = []
    for _ in range(3):
        for route in ("start", "woche", "lernen", "links", "faecher", "lesen"):
            page.evaluate(f"location.hash='#{route}'"); page.wait_for_timeout(200)
        counts.append(page.evaluate("document.querySelectorAll('filter[id^=rb-lgr]').length"))
    page.close()
    assert counts[0] == counts[-1], f"Filter wachsen beim Navigieren: {counts}"


def check_brand_contrast(browser, url):
    for theme in ("dunkel", "mittel"):
        page = browser.new_page(viewport={"width": 820, "height": 1180}, color_scheme="dark")
        page.goto(url + "#start"); page.wait_for_timeout(1000)
        page.evaluate(f"document.documentElement.dataset.theme='{theme}'"); page.wait_for_timeout(200)
        fg = page.evaluate("getComputedStyle(document.querySelector('#brand-home .rb-current')).color")
        box = page.locator('#brand-home .rb-current').bounding_box()
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(page.screenshot(clip={"x": box["x"] + box["width"] + 2, "y": box["y"], "width": 4, "height": box["height"]}))).convert("RGB")
        bg = img.getpixel((1, img.height // 2))
        nums = [float(v) for v in re.findall(r"[\d.]+", fg.replace("srgb", ""))[:3]]
        text = tuple(int(round(v * 255)) if fg.startswith("color(") else int(v) for v in nums)
        l1, l2 = sorted((lum(text), lum(bg)), reverse=True)
        ratio = (l1 + .05) / (l2 + .05)
        page.close()
        assert ratio >= 4.5, f"Kontrast „Start“ in {theme}: {ratio:.2f}:1"


def check_reader_without_glass(browser, url):
    page = browser.new_page(viewport={"width": 1180, "height": 820})
    page.goto(url); page.wait_for_timeout(800)
    import base64, io
    from reportlab.pdfgen.canvas import Canvas
    s = io.BytesIO(); c = Canvas(s, pagesize=(595, 842)); c.drawString(60, 760, "Seite"); c.showPage(); c.save()
    page.evaluate("""async enc => { view='skr'; const b=Uint8Array.from(atob(enc),c=>c.charCodeAt(0));
        await skAdd([new File([b],'S.pdf',{type:'application/pdf'})]); await skOpen(S.scripts[0].id); }""", base64.b64encode(s.getvalue()).decode())
    page.wait_for_selector(".pg .ink-overlay")
    page.evaluate("document.documentElement.style.setProperty('--liquid',1);document.documentElement.style.setProperty('--paper-glass',1)")
    filters = page.evaluate("[...document.querySelectorAll('#sv .svb,#sv .ink-dock')].map(e=>[getComputedStyle(e).backdropFilter,getComputedStyle(e,'::before').content])")
    page.close()
    assert all(f == "none" and pc in ("none", "normal") for f, pc in filters), f"Glas im Reader: {filters}"


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    handler = partial(SimpleHTTPRequestHandler, directory=root)
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get("CHROMIUM") or shutil.which("chromium"))
            url = f"http://127.0.0.1:{server.server_port}/"
            results = []
            for name, fn in (("Keine Filter-Ansammlung", check_no_filter_growth),
                             ("Kontrast Markenzusatz", check_brand_contrast),
                             ("Reader ohne Glas", check_reader_without_glass)):
                try: fn(browser, url); results.append(f"OK    {name}")
                except Exception as e: results.append(f"FEHLER {name}: {str(e).splitlines()[0][:160]}")
            browser.close()
        server.shutdown()
    print("\n".join(results))
    raise SystemExit(any(r.startswith("FEHLER") for r in results))
