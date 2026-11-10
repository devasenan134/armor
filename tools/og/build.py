#!/usr/bin/env python3
"""Regenerate site/assets/og.png from the live copy in site/index.html.

The headline and availability chip are read from the main page, so the
link-preview image follows the page instead of drifting from it.
Only the tagline and domain live in tools/og/og.json.

    python3 tools/og/build.py           # render if inputs changed
    python3 tools/og/build.py --force   # render regardless
    python3 tools/og/build.py --check   # exit 1 if og.png or its URL version is stale (no writes)

The og:image URL in both pages carries ?v=<hash of og.png>, rewritten whenever
the image changes, so LinkedIn, Slack and WhatsApp refetch a new image instead
of serving a cached one.

Needs python3 (standard library only) and one Chromium-based browser
(Playwright's Chromium, Chrome, Chromium or Brave). Fonts load from
Google Fonts, same as the site, so the first render needs a network.
"""
import hashlib, html, json, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
PAGE = ROOT / "site" / "index.html"
OUT = ROOT / "site" / "assets" / "og.png"
PAGES = [ROOT / "site" / "index.html", ROOT / "site" / "minecraft" / "index.html"]
OG_META = re.compile(r'(<meta property="og:image" content="[^"]*?/assets/og\.png)(?:\?v=[0-9a-f]+)?(")')
STAMP = HERE / ".last-build"


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def read_inputs():
    src = PAGE.read_text(encoding="utf-8")
    m = re.search(r"<h1>(.*?)</h1>", src, re.S)
    if not m:
        sys.exit("Could not find the <h1> in site/index.html")
    h1 = m.group(1)
    line1, rest = re.split(r"<br\s*/?>", h1, maxsplit=1)
    m = re.search(r'<span class="chip"><i></i>(.*?)</span>', src, re.S)
    if not m:
        sys.exit("Could not find the availability chip in site/index.html")
    chip = m.group(1)
    chip = clean(chip).split(" · ")[0]  # drop the city, it is shown bottom right
    cfg = json.loads((HERE / "og.json").read_text(encoding="utf-8"))
    return {
        "line1": clean(line1), "line2": clean(rest), "chip": chip,
        "name": cfg["name"], "initials": cfg["initials"], "tagline": cfg["tagline"],
        "domain": cfg["domain"], "location": cfg["location"],
    }


def digest(inp):
    blob = json.dumps(inp, sort_keys=True) + (HERE / "og.template.html").read_text(encoding="utf-8")
    return hashlib.sha256(blob.encode()).hexdigest()


def find_browser():
    home = pathlib.Path.home()
    cands = sorted(home.glob("Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"))
    cands += sorted(home.glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))
    cands += [pathlib.Path(p) for p in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/usr/bin/chromium", "/usr/bin/google-chrome")]
    for c in cands:
        if c.exists():
            return str(c)
    sys.exit("No Chromium-based browser found.")


def render(inp):
    longest = max(len(inp["line1"]), len(inp["line2"]))
    size = int(min(88, 1040 / (longest * 0.43)))
    tpl = (HERE / "og.template.html").read_text(encoding="utf-8")
    rep = {"__H1_SIZE__": str(size), "__INITIALS__": inp["initials"], "__NAME__": inp["name"],
           "__CHIP__": inp["chip"], "__H1_LINE1__": inp["line1"], "__H1_LINE2__": inp["line2"],
           "__TAGLINE__": inp["tagline"], "__DOMAIN__": inp["domain"], "__LOCATION__": inp["location"]}
    for k, v in rep.items():
        tpl = tpl.replace(k, v if k == "__H1_SIZE__" else html.escape(v, quote=False))
    with tempfile.TemporaryDirectory() as td:
        page = pathlib.Path(td) / "og.html"
        page.write_text(tpl, encoding="utf-8")
        shot = pathlib.Path(td) / "og.png"
        cmd = [find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--force-device-scale-factor=1", "--window-size=1200,630",
               "--virtual-time-budget=8000", f"--screenshot={shot}", page.as_uri()]
        try:
            subprocess.run(cmd, check=True, timeout=60, capture_output=True)
        except subprocess.TimeoutExpired:
            if not shot.exists():
                sys.exit("Browser timed out before writing a screenshot.")
        if not shot.exists():
            sys.exit("Browser did not produce a screenshot.")
        OUT.write_bytes(shot.read_bytes())


def sync_urls(write):
    """Make every page's og:image URL carry the current image hash."""
    v = hashlib.sha256(OUT.read_bytes()).hexdigest()[:8]
    stale = []
    for p in PAGES:
        src = p.read_text(encoding="utf-8")
        if not OG_META.search(src):
            sys.exit(f"No og:image meta found in {p.relative_to(ROOT)}")
        out = OG_META.sub(lambda m: f"{m.group(1)}?v={v}{m.group(2)}", src)
        if out != src:
            stale.append(p)
            if write:
                p.write_text(out, encoding="utf-8")
    return v, stale


def main():
    inp = read_inputs()
    d = digest(inp)
    inputs_ok = OUT.exists() and (not STAMP.exists() or STAMP.read_text().strip() == d)
    if "--check" in sys.argv:
        if not OUT.exists():
            print("og.png is missing")
            sys.exit(1)
        v, stale = sync_urls(False)
        ok = inputs_ok and not stale
        print(f"og.png is up to date (v={v})" if ok else "og.png or its URL version is STALE: run tools/og/build.py")
        sys.exit(0 if ok else 1)
    if inputs_ok and STAMP.exists() and "--force" not in sys.argv:
        print("og.png already matches the page; no render needed")
    else:
        render(inp)
        STAMP.write_text(d + "\n")
        print(f"rendered {OUT.relative_to(ROOT)}: {inp['line1']} / {inp['line2']}")
    v, stale = sync_urls(True)
    print(f"og:image version v={v}; updated {len(stale)} page(s)")


if __name__ == "__main__":
    main()
