// AI 판정: 파일을 Vercel 함수(GRADER_URL=/api)로 보내면 함수가 Upstage Document Parse(OCR) → Solar 칸별 추출 → 규칙 판정을 수행한다.
// Upstage 키는 Vercel 환경변수에만 있다. 한 건씩 또는 여러 건을 차례로 판정할 수 있다.
(function () {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const BADGE = { "고위험": "b-고위험", "중위험": "b-중위험", "저위험": "b-저위험", "검토 필요": "b-검토" };
  const ACTION = {
    "고위험": "발송 차단·보고 — 발송을 멈추고 노출된 번호를 개인정보보호 책임자에게 보고합니다.",
    "중위험": "마스킹 요청 — 노출된 항목을 가린 뒤 다시 제출하도록 요청합니다.",
    "저위험": "발송 승인 기록 — 노출 항목이 없어 발송 가능으로 기록합니다.",
    "검토 필요": "담당자 확인 요청 — 판독할 수 없거나 재식별 위험이 있어 담당자가 원본을 직접 확인합니다.",
  };
  const MAX = 4 * 1024 * 1024;
  const GRADER = (window.GRADER_URL || "").replace(/\/$/, "");
  const CASES = window.CASES || [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // 샘플 목록에는 정답을 넣지 않는다 (정답은 판정 뒤 결과와 함께 보여 줌)
  CASES.forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id;
    o.textContent = `${c.set} · ${c.docs.join(", ")}`;
    $("sample").appendChild(o);
  });
  if (CASES.length) $("sample").value = CASES[0].id;
  $("file").addEventListener("change", () => {
    const n = $("file").files.length;
    if (n) $("sample").value = "";
    $("aiRun").textContent = n > 1 ? `파일 ${n}개 한꺼번에 판정` : "AI로 판정하기";
  });

  const setStep = (st) => document.querySelectorAll("#aiSteps li").forEach((li) => (st ? li.setAttribute("data-st", st) : li.removeAttribute("data-st")));
  const norm = (a) => [...new Set((a || []).map((x) => String(x).trim()))].sort().join(",");
  const matches = (k, out) => ({
    lvl: k.risk_level === out.risk_level,
    items: norm(k.detected_items) === norm(out.detected_items),
    subj: k.data_subject === out.data_subject,
  });

  // 실패하면 무엇이 문제인지와 다음에 할 일을 함께 보여 준다
  function guide(status, msg) {
    if (status === 429) return "1분 뒤에 다시 눌러 주세요. 판정 요청이 한꺼번에 많이 몰렸습니다.";
    if (status === 413) return "4MB 이하 파일로 다시 올려 주세요. 쪽수를 줄이거나 해상도를 낮추면 됩니다.";
    if (status === 403) return "이 사이트 주소에서 직접 열어 사용해 주세요.";
    if (status === 400) return "PDF나 이미지 파일을 다시 골라 주세요.";
    if (status === 0) return "인터넷 연결을 확인한 뒤 다시 시도해 주세요.";
    if (/키가 설정/.test(msg)) return "운영 중인 판정 서버 설정 문제입니다. 잠시 뒤 다시 시도해 주세요.";
    return "잠시 뒤 다시 시도해 주세요. 같은 문제가 계속되면 다른 샘플로 먼저 확인해 보세요.";
  }

  // 한 건 판정: 요청이 몰려 429가 나면 기다렸다가 자동으로 다시 보낸다
  async function gradeOne(blob, name, onWait) {
    if (blob.size > MAX) return { ok: false, status: 413, error: "파일이 4MB보다 큽니다." };
    for (let attempt = 0; attempt < 5; attempt++) {
      const fd = new FormData();
      fd.append("document", blob, name);
      let res;
      try { res = await fetch(`${GRADER}/grade`, { method: "POST", body: fd }); }
      catch (e) { return { ok: false, status: 0, error: "판정 서버에 연결하지 못했습니다." }; }
      let j = {};
      try { j = await res.json(); } catch (e) {}
      if (res.status === 429 && attempt < 4) { onWait && onWait(20); await sleep(20000); continue; }
      if (!res.ok || !j.result) return { ok: false, status: res.status, error: j.error || `서버 오류 (HTTP ${res.status})`, ocr: j.ocr };
      return { ok: true, result: j.result, ocr: j.ocr, raw: j.raw || "" };
    }
    return { ok: false, status: 429, error: "요청이 너무 많습니다." };
  }

  async function sampleBlob(c) {
    const r = await fetch(c.file).catch(() => null);
    if (!r || !r.ok) throw new Error("샘플 파일을 불러오지 못했습니다.");
    return r.blob();
  }

  // 결과 한 건을 화면용 HTML로
  function detailHtml(out, ocr, raw, kase, job) {
    const lvl = out.risk_level || "?";
    const items = Array.isArray(out.detected_items) ? out.detected_items : [];
    let h = `<span class="note">판정 결과</span><div class="lvl"><span class="badge ${BADGE[lvl] || ""}" style="font-size:24px;padding:4px 16px">${esc(lvl)}</span></div>`;
    h += `<p><b>담당자가 할 일:</b> ${esc(ACTION[lvl] || "-")}</p>`;
    h += `<p><b>가려지지 않은 항목:</b> ${items.length ? esc(items.join(", ")) : "없음"}<br><b>누구의 정보인가:</b> ${esc(out.data_subject || "-")}</p>`;
    h += `<p><b>판정 근거:</b> ${esc(out.reason || "")}</p>`;
    if (kase) {
      const m = matches(kase, out), x = (b) => (b ? "✅" : "❌");
      h += `<div class="cmp"><b>정답과 비교 (${esc(kase.set)})</b><br>${x(m.lvl)} 위험도: 정답 ${esc(kase.risk_level)}<br>${x(m.items)} 노출 항목: 정답 ${esc(kase.detected_items.join(", ") || "없음")}<br>${x(m.subj)} 정보 주체: 정답 ${esc(kase.data_subject)}<br><span class="note">${m.lvl && m.items && m.subj ? "세 항목 모두 정답과 같습니다." : "일부가 정답과 다릅니다. OCR이 일부 칸을 다르게 읽었을 수 있으니 아래 ‘서식별 추출 결과’에서 어느 값이 달랐는지 확인해 보세요."}</span></div>`;
    }
    h += maskHtml(out, job);
    h += evidenceHtml(out);
    const docs = Array.isArray(out.documents) ? out.documents : [];
    h += `<details><summary>서식별 추출 원본(JSON) 보기 (${docs.length}개)</summary><pre class="raw">${esc(JSON.stringify(docs, null, 2))}</pre></details>`;
    if (ocr) h += `<details><summary>문서에서 읽은 글자 보기 (${esc(ocr.pages)}쪽)</summary><pre class="raw">${esc(ocr.text)}</pre></details>`;
    if (raw) h += `<details><summary>모델 원문 응답 (개발자용)</summary><pre class="raw">${esc(raw)}</pre></details>`;
    return h;
  }
  // 판정 과정(단계별 확인)과 서식별 노출·가린 값 표
  function evidenceHtml(out) {
    const ev = out.evidence;
    if (!ev) return "";
    const lvl = out.risk_level, c = ev.checks || {};
    const docs = ev.documents || [];
    const exposedHigh = docs.flatMap((d) => d.skipped ? [] : d.items.filter((x) => x.tier === "고위험" && x.exposed.length).map((x) => x.item));
    const exposedMid = docs.flatMap((d) => d.skipped ? [] : d.items.filter((x) => x.tier === "중위험" && x.exposed.length).map((x) => x.item));
    const uniq = (a) => [...new Set(a)];
    const step = (hit, title, detail) => `<li style="margin:4px 0">${hit ? "●" : "○"} <b>${esc(title)}</b> — <span class="${hit ? "" : "note"}">${esc(detail)}</span></li>`;
    let h = `<h4 style="margin:16px 0 4px">판정 과정</h4><ol style="list-style:none;padding-left:0;margin:0;font-size:14px">`;
    h += step(c.unreadable && c.unreadable.length, "1-a 판독 불가", c.unreadable && c.unreadable.length ? `${c.unreadable.join(", ")} — 흐리거나 칸을 읽을 수 없음` : "모든 서식을 읽을 수 있음");
    h += step(c.empty_read && c.empty_read.length, "1-b 내용 판독 실패", c.empty_read && c.empty_read.length ? "제목과 번호·이름 칸이 하나도 읽히지 않은 서식이 있음" : "제목이나 값이 읽힘");
    h += step(c.reidentify && c.reidentify.length, "1-c 재식별 위험", c.reidentify && c.reidentify.length ? c.reidentify.map((r) => `${r.doc}: 이름(${r.names.join(", ")})은 가렸지만 ${r.clues.join(", ")}`).join(" / ") : "해당 없음");
    h += step(exposedHigh.length && lvl !== "검토 필요", "2 고위험 항목 노출", exposedHigh.length ? uniq(exposedHigh).join(", ") : "주민·외국인등록·여권·운전면허·카드번호 노출 없음");
    h += step(!exposedHigh.length && exposedMid.length && lvl !== "검토 필요", "3 중위험 항목 노출", exposedMid.length ? uniq(exposedMid).join(", ") : "계좌·휴대전화·주소·이메일·소득·신용·기업재무 노출 없음");
    h += step(lvl === "저위험", "4 저위험", lvl === "저위험" ? "가려지지 않은 민감정보 없음" : "해당 없음");
    h += `</ol><p class="note" style="margin:4px 0 0">● 표시가 처음 나온 단계에서 등급이 정해집니다.</p>`;

    h += `<h4 style="margin:16px 0 4px">서식별 확인 결과 (${docs.length}개)</h4>`;
    docs.forEach((d) => {
      h += `<div class="one"><b>${esc(d.title)}</b> <span class="note">${esc(d.owner_type)} 서류 · 판독 ${d.readability === "unclear" ? "불가" : "가능"}${d.masking_stamp ? " · ‘마스킹 처리본’ 표시 있음" : ""}${d.skipped ? ` · ${esc(d.skipped)}로 노출 판단에서 제외` : ""}</span>`;
      if (!d.items.length) { h += `<p class="note" style="margin:4px 0">민감정보 칸에서 읽힌 값이 없습니다.</p></div>`; return; }
      h += `<div class="scroll" style="margin-top:6px"><table class="batch"><thead><tr><th>항목</th><th>등급</th><th>가려지지 않은 값 (노출)</th><th>가린 값 (노출 아님)</th></tr></thead><tbody>`;
      d.items.forEach((x) => {
        h += `<tr><td>${esc(x.item)}</td><td><span class="badge ${x.exposed.length ? BADGE[x.tier] : ""}">${esc(x.tier)}</span></td><td class="${x.exposed.length ? "err" : "note"}">${x.exposed.length ? x.exposed.map(esc).join("<br>") : "—"}</td><td class="note">${x.masked.length ? x.masked.map(esc).join("<br>") : "—"}</td></tr>`;
      });
      h += `</tbody></table></div></div>`;
    });
    return h;
  }

  // ---- 가린 PDF 만들기 ----
  // 노출된 값의 위치를 /api/mask(Upstage OCR 단어 좌표)로 찾고, 브라우저에서 쪽을 그림으로 그려 그 자리를 검게 칠한 PDF를 만든다.
  // 쪽을 그림으로 바꾸므로 가린 글자가 PDF 안에 텍스트로 남지 않는다. 파일은 판정 서버 외에는 어디로도 보내지 않는다.
  const jobs = [];
  const exposedValues = (out) => [...new Set(((out.evidence || {}).documents || []).flatMap((d) => d.items.flatMap((x) => x.exposed)).map(String))];
  function maskHtml(out, job) {
    if (job == null) return "";
    const vals = exposedValues(out);
    if (!vals.length) return `<p class="note">가려야 할 노출 값이 없어 가린 PDF는 만들 필요가 없습니다.</p>`;
    return `<div class="cmp"><b>가린 PDF 만들기</b> <span class="note">노출된 값 ${vals.length}개를 검게 가린 PDF를 내려받습니다. (쪽을 그림으로 바꿔 가린 글자가 남지 않음)</span><div class="btns"><button type="button" data-mask="${job}">가린 PDF 만들기</button></div><div class="mask-st" data-mask-st="${job}"></div></div>`;
  }
  const loaded = {};
  const loadScript = (src) => (loaded[src] ??= new Promise((ok, no) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = () => no(new Error("PDF 도구를 불러오지 못했습니다.")); document.head.appendChild(s); }));
  const PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/";
  async function libs() {
    await Promise.all([loadScript(PDFJS + "pdf.min.js"), loadScript("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js")]);
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS + "pdf.worker.min.js";
    return { pdfjs: window.pdfjsLib, JsPDF: window.jspdf.jsPDF };
  }
  async function findBoxes(blob, name, values, onWait) {
    for (let attempt = 0; attempt < 5; attempt++) {
      const fd = new FormData(); fd.append("document", blob, name); fd.append("values", JSON.stringify(values));
      let res; try { res = await fetch(`${GRADER}/mask`, { method: "POST", body: fd }); } catch (e) { throw new Error("판정 서버에 연결하지 못했습니다."); }
      let j = {}; try { j = await res.json(); } catch (e) {}
      if (res.status === 429 && attempt < 4) { onWait(20); await sleep(20000); continue; }
      if (!res.ok || !j.pages) throw new Error(j.error || `서버 오류 (HTTP ${res.status})`);
      return j;
    }
    throw new Error("요청이 너무 많습니다. 1분 뒤 다시 시도하세요.");
  }
  // 파일의 쪽을 캔버스로 (PDF는 pdf.js, 사진은 그대로)
  async function pageCanvases(blob, pdfjs) {
    const isPdf = /pdf/i.test(blob.type) || new Uint8Array(await blob.slice(0, 4).arrayBuffer()).join() === "37,80,68,70";
    const list = [];
    if (isPdf) {
      const doc = await pdfjs.getDocument({ data: await blob.arrayBuffer() }).promise;
      for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i), vp1 = page.getViewport({ scale: 1 }), vp = page.getViewport({ scale: 2 });
        const c = document.createElement("canvas"); c.width = vp.width; c.height = vp.height;
        await page.render({ canvasContext: c.getContext("2d"), viewport: vp }).promise;
        list.push({ c, wPt: vp1.width, hPt: vp1.height });
      }
    } else {
      const img = await createImageBitmap(blob), c = document.createElement("canvas");
      c.width = img.width; c.height = img.height; c.getContext("2d").drawImage(img, 0, 0);
      const s = 595 / Math.max(img.width, 1);
      list.push({ c, wPt: 595, hPt: img.height * s });
    }
    return list;
  }
  async function makeMasked(job, btn) {
    const j = jobs[job], st = document.querySelector(`[data-mask-st="${job}"]`);
    const say = (t, cls = "note") => { st.innerHTML = `<p class="${cls}" style="margin:6px 0 0">${t}</p>`; };
    btn.disabled = true;
    try {
      const values = exposedValues(j.out);
      say("노출된 값의 위치를 찾는 중… (10~30초)");
      const blob = await j.get();
      const [found, { pdfjs, JsPDF }] = await Promise.all([findBoxes(blob, j.name, values, (s) => say(`요청이 몰려 ${s}초 기다렸다가 다시 보냅니다…`)), libs()]);
      say("쪽을 그리고 가리는 중…");
      const pages = await pageCanvases(blob, pdfjs);
      let pdf = null, n = 0;
      pages.forEach((p, i) => {
        const g = p.c.getContext("2d"), W = p.c.width, H = p.c.height, pad = 0.004;
        g.fillStyle = "#000";
        ((found.pages[i] || {}).boxes || []).forEach((b) => { g.fillRect((b.x - pad) * W, (b.y - pad) * H, (b.w + 2 * pad) * W, (b.h + 2 * pad) * H); n++; });
        const o = p.wPt > p.hPt ? "l" : "p";
        if (!pdf) pdf = new JsPDF({ orientation: o, unit: "pt", format: [p.wPt, p.hPt] });
        else pdf.addPage([p.wPt, p.hPt], o);
        pdf.addImage(p.c.toDataURL("image/jpeg", 0.85), "JPEG", 0, 0, p.wPt, p.hPt);
      });
      const file = j.name.replace(/\.[^.]+$/, "") + "_가림.pdf";
      pdf.save(file);
      const miss = found.missing || [];
      say(`${pages.length}쪽에서 ${n}곳을 가려 <b>${esc(file)}</b>로 내려받았습니다.` +
        (miss.length ? `<br><span class="err">위치를 찾지 못해 가리지 못한 값 ${miss.length}개: ${miss.map(esc).join(", ")} — 내려받은 파일에서 직접 확인해 주세요.</span>` : " 노출된 값을 모두 찾아 가렸습니다. 발송 전 한 번 더 눈으로 확인해 주세요."));
    } catch (e) {
      say(`가린 PDF를 만들지 못했습니다. ${esc(e.message)} — 잠시 뒤 다시 눌러 주세요.`, "err");
    }
    btn.disabled = false;
  }
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-mask]"); if (b) makeMasked(+b.dataset.mask, b); });

  function failHtml(r) {
    return `<p class="err"><b>판정하지 못했습니다.</b> ${esc(r.error)}</p><p><b>이렇게 해 보세요:</b> ${esc(guide(r.status, r.error))}</p>`;
  }

  // ---- 한 건씩 ----
  async function runOne() {
    const out = $("aiOut");
    if (!GRADER) { out.innerHTML = failHtml({ status: -1, error: "판정 서버 주소가 설정되지 않았습니다." }); return; }
    const files = [...$("file").files];
    if (files.length > 1) return runBatch(files.map((f) => ({ name: f.name, get: async () => f })));
    const kase = CASES.find((c) => c.id === $("sample").value);
    let blob, name;
    try {
      if (kase) { blob = await sampleBlob(kase); name = kase.set + ".pdf"; }
      else if (files.length) { blob = files[0]; name = blob.name; }
      else { out.innerHTML = '<p class="err">판정할 서류가 없습니다.</p><p><b>이렇게 해 보세요:</b> 위 목록에서 샘플을 고르거나 PDF·사진 파일을 올려 주세요.</p>'; return; }
    } catch (e) { out.innerHTML = failHtml({ status: 0, error: e.message }); return; }

    busy(true); setStep("run");
    out.innerHTML = `<span class="note">${esc(name)} 판정 중… 보통 20~60초 걸립니다. 창을 닫지 말고 기다려 주세요.</span>`;
    const r = await gradeOne(blob, name, (s) => { out.innerHTML = `<span class="note">요청이 몰려 ${s}초 기다렸다가 다시 보냅니다…</span>`; });
    busy(false);
    if (!r.ok) {
      setStep("err");
      out.innerHTML = failHtml(r) + `<div class="btns"><button type="button" id="aiRetry">다시 판정하기</button></div>` +
        (r.ocr && r.ocr.text ? `<details><summary>문서에서 읽은 글자 보기</summary><pre class="raw">${esc(r.ocr.text)}</pre></details>` : "");
      $("aiRetry").addEventListener("click", runOne);
      return;
    }
    setStep("ok");
    jobs.push({ get: async () => blob, name, out: r.result });
    out.innerHTML = detailHtml(r.result, r.ocr, r.raw, kase, jobs.length - 1);
  }

  // ---- 여러 건 한꺼번에 ----
  let rows = [];
  function drawBatch(done) {
    const ok = rows.filter((r) => r.res && r.res.ok);
    const withAns = ok.filter((r) => r.kase);
    const allMatch = withAns.filter((r) => { const m = matches(r.kase, r.res.result); return m.lvl && m.items && m.subj; });
    const count = (lv) => ok.filter((r) => r.res.result.risk_level === lv).length;
    let h = `<h3 style="margin:24px 0 8px">한꺼번에 판정 (${rows.filter((r) => r.res).length}/${rows.length}건 완료)</h3>`;
    h += `<div class="batch-sum">${["고위험", "중위험", "저위험", "검토 필요"].map((lv) => `<span class="badge ${BADGE[lv]}">${lv} ${count(lv)}</span>`).join("")}`;
    if (withAns.length) h += `<span class="note">정답과 세 항목 모두 일치 ${allMatch.length}/${withAns.length}건</span>`;
    if (done) h += ` <button type="button" id="csvBtn">결과 CSV 내려받기</button>`;
    h += `</div><div class="scroll"><table class="batch"><thead><tr><th>서류</th><th>위험도</th><th>가려지지 않은 항목</th><th>담당자가 할 일</th>${withAns.length || rows.some((r) => r.kase) ? "<th>정답</th>" : ""}<th></th></tr></thead><tbody>`;
    rows.forEach((r, i) => {
      const hasAns = rows.some((x) => x.kase);
      if (!r.res) { h += `<tr><td>${esc(r.name)}</td><td colspan="${hasAns ? 5 : 4}" class="st">${esc(r.state || "대기 중")}</td></tr>`; return; }
      if (!r.res.ok) { h += `<tr><td>${esc(r.name)}</td><td colspan="${hasAns ? 4 : 3}" class="err">${esc(r.res.error)} — ${esc(guide(r.res.status, r.res.error))}</td><td><button type="button" data-retry="${i}">다시</button></td></tr>`; return; }
      const o = r.res.result, m = r.kase ? matches(r.kase, o) : null;
      h += `<tr class="${r.open ? "open" : ""}"><td>${esc(r.name)}</td><td><span class="badge ${BADGE[o.risk_level] || ""}">${esc(o.risk_level)}</span></td><td>${esc((o.detected_items || []).join(", ") || "없음")}</td><td>${esc((ACTION[o.risk_level] || "").split(" — ")[0])}</td>${hasAns ? `<td>${m ? (m.lvl && m.items && m.subj ? "✅ 일치" : "❌ 다름") : "—"}</td>` : ""}<td><button type="button" data-open="${i}">${r.open ? "접기" : "자세히"}</button></td></tr>`;
      if (r.open) {
        if (r.job == null || jobs[r.job].out !== o) { jobs.push({ get: r.get, name: r.kase ? r.kase.set + ".pdf" : r.name, out: o }); r.job = jobs.length - 1; }
        h += `<tr class="open"><td colspan="${hasAns ? 6 : 5}"><div class="result">${detailHtml(o, r.res.ocr, "", r.kase, r.job)}</div></td></tr>`;
      }
    });
    h += `</tbody></table></div>`;
    $("batchOut").innerHTML = h;
    $("batchOut").querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => { const r = rows[+b.dataset.open]; r.open = !r.open; drawBatch(done); }));
    $("batchOut").querySelectorAll("[data-retry]").forEach((b) => b.addEventListener("click", async () => {
      const r = rows[+b.dataset.retry]; r.res = null; r.state = "다시 판정 중…"; drawBatch(false);
      r.res = await gradeOne(await r.get(), r.name, (s) => { r.state = `요청이 몰려 ${s}초 기다리는 중…`; drawBatch(false); });
      drawBatch(true);
    }));
    const csv = $("csvBtn");
    if (csv) csv.addEventListener("click", downloadCsv);
  }

  function downloadCsv() {
    const q = (s) => `"${String(s ?? "").replace(/"/g, '""')}"`;
    const lines = [["서류", "위험도", "가려지지 않은 항목", "정보 주체", "담당자가 할 일", "판정 근거"].map(q).join(",")];
    rows.forEach((r) => {
      if (r.res && r.res.ok) { const o = r.res.result; lines.push([r.name, o.risk_level, (o.detected_items || []).join(", "), o.data_subject, ACTION[o.risk_level] || "", o.reason].map(q).join(",")); }
      else lines.push([r.name, "판정 실패", "", "", "", r.res ? r.res.error : ""].map(q).join(","));
    });
    const url = URL.createObjectURL(new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = "민감정보_판정결과.csv"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function runBatch(list) {
    if (!GRADER) { $("aiOut").innerHTML = failHtml({ status: -1, error: "판정 서버 주소가 설정되지 않았습니다." }); return; }
    rows = list.map((x) => ({ ...x, res: null, state: "대기 중", open: false }));
    busy(true); setStep("run");
    $("aiOut").innerHTML = `<span class="note">${rows.length}건을 차례로 판정합니다. 결과는 아래 표에 하나씩 채워집니다. 한 건에 20~60초쯤 걸립니다.</span>`;
    drawBatch(false);
    let next = 0;
    const worker = async () => {
      while (next < rows.length) {
        const r = rows[next++];
        r.state = "판정 중…"; drawBatch(false);
        try { r.res = await gradeOne(await r.get(), r.name, (s) => { r.state = `요청이 몰려 ${s}초 기다리는 중…`; drawBatch(false); }); }
        catch (e) { r.res = { ok: false, status: 0, error: e.message }; }
        drawBatch(false);
      }
    };
    await Promise.all([worker(), worker()]); // 동시에 2건씩
    busy(false);
    setStep(rows.every((r) => r.res && r.res.ok) ? "ok" : "err");
    $("aiOut").innerHTML = `<span class="note">${rows.length}건 판정을 마쳤습니다. 아래 표에서 ‘자세히’를 누르면 건별 근거를 볼 수 있습니다.</span>`;
    drawBatch(true);
  }

  function busy(b) { $("aiRun").disabled = b; $("aiAll").disabled = b; }

  $("aiRun").addEventListener("click", runOne);
  $("aiAll").addEventListener("click", () => runBatch(CASES.map((c) => ({ name: `${c.set} · ${c.docs.join(", ")}`, kase: c, get: () => sampleBlob(c) }))));
})();
