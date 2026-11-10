# Playwright driver: runs Edge with a persistent profile and executes command files.
import sys, time, traceback, io, contextlib
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent
VIDEO = len(sys.argv) > 1 and sys.argv[1] == "record"
CMD, OUT = BASE / "cmd.py", BASE / "out.txt"

with sync_playwright() as p:
    kw = dict(user_data_dir=str(BASE / "profile"), channel="msedge", headless=False,
              viewport={"width": 1440, "height": 900}, locale="ko-KR", args=["--window-size=1460,1000"])
    if VIDEO:
        kw.update(record_video_dir=str(BASE / "video"), record_video_size={"width": 1440, "height": 900})
    ctx = p.chromium.launch_persistent_context(**kw); T0 = time.time()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if not VIDEO:
        page.goto("https://studio.upstage.ai/agents/agt_QNRagA4yve25i7ciZiCSE2?configVer=1&view=table")
    (BASE / "ready.txt").write_text("ready", encoding="utf-8")
    g = {"page": page, "ctx": ctx, "time": time, "BASE": BASE, "T0": T0}
    while True:
        if CMD.exists():
            src = CMD.read_text(encoding="utf-8"); CMD.unlink()
            if src.strip() == "QUIT":
                break
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(src, g)
                res = "OK\n" + buf.getvalue()
            except Exception:
                res = "ERR\n" + buf.getvalue() + traceback.format_exc()
            OUT.write_text(res, encoding="utf-8")
        time.sleep(0.2)
    page.close()
    ctx.close()
    (BASE / "closed.txt").write_text("closed", encoding="utf-8")
