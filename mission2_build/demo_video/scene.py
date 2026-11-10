# Full demo recording. Writes scene marks (seconds since video start) to marks.json.
import json
T0 = globals().get("T0") or time.time()
marks = []
def mark(name):
    marks.append([name, round(time.time() - T0, 2)])
    (BASE / "marks.json").write_text(json.dumps(marks, ensure_ascii=False), encoding="utf-8")
def hold(s): time.sleep(s)
def smooth_scroll(sel, dy, steps=12):
    for _ in range(steps):
        page.mouse.wheel(0, dy / steps); time.sleep(0.08)

# ---------- Studio: 모아보기(20 files)
page.goto("https://studio.upstage.ai/agents/agt_QNRagA4yve25i7ciZiCSE2?configVer=1&view=table")
page.get_by_text("요미의 코딩_최종제출_set18.pdf").first.wait_for(timeout=90000)
hold(2); mark("table")
hold(5)
page.mouse.move(700, 500); smooth_scroll(None, 600); hold(2); smooth_scroll(None, -600); hold(1)
mark("table_end")

# ---------- 상세보기 set17
page.get_by_role("button", name="상세보기").click()
page.get_by_text("요미의 코딩_최종제출_set17.pdf").first.wait_for(timeout=60000)
hold(2)
page.get_by_text("요미의 코딩_최종제출_set17.pdf").first.click(); hold(3)
mark("parse")
page.get_by_text("Parse", exact=True).first.click(); hold(5)
page.mouse.move(1120, 600); smooth_scroll(None, 500); hold(2)
mark("classify")
page.get_by_text("Classify", exact=True).first.click(); hold(6)
mark("extract")
page.get_by_text("Extract", exact=True).first.click(); hold(5)
# personal_doc under set17 (second sub-row of the selected file)
y17 = page.get_by_text("요미의 코딩_최종제출_set17.pdf").first.bounding_box()["y"]
for i in range(page.get_by_text("personal_doc", exact=True).count()):
    el = page.get_by_text("personal_doc", exact=True).nth(i); b = el.bounding_box()
    if b and y17 < b["y"] < y17 + 130 and b["x"] < 380:
        el.click(); break
hold(5)
mark("validate")
page.get_by_text("Validate", exact=True).first.click(); hold(6)
mark("judge")
page.get_by_text("Instruct", exact=True).nth(0).click(); hold(9)
mark("followup")
page.get_by_text("Instruct", exact=True).nth(1).click(); hold(8)
mark("studio_end")

# ---------- Site
page.goto("https://yomicoding-site.vercel.app/"); hold(3)
mark("site")
page.locator("#ai").scroll_into_view_if_needed(); hold(2)
page.select_option("#sample", index=[o for o in range(page.locator("#sample option").count()) if page.locator("#sample option").nth(o).inner_text().startswith("set09")][0])
hold(2)
page.click("#aiRun")
mark("site_wait")
page.locator("#aiOut .lvl").wait_for(timeout=180000)
mark("site_result")
hold(3)
page.locator("#aiOut").scroll_into_view_if_needed(); page.mouse.move(1000, 500)
for _ in range(3):
    smooth_scroll(None, 300); hold(1.5)
hold(2)
mark("mask")
btn = page.locator("[data-mask]").first
btn.scroll_into_view_if_needed(); hold(1.5)
with page.expect_download(timeout=180000) as dl:
    btn.click()
d = dl.value
out = BASE / "masked.pdf"; d.save_as(str(out))
hold(2)
mark("masked_view")
page.goto(out.as_uri()); hold(7)
mark("end")
print(json.dumps(marks, ensure_ascii=False))
