// AI 판정: Upstage Document Parse(OCR) → Solar(추출+판정). 키는 브라우저에서 Upstage API로만 전송된다.
(function () {
  const API = "https://api.upstage.ai/v1";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const BADGE = { "고위험": "b-고위험", "중위험": "b-중위험", "저위험": "b-저위험", "검토 필요": "b-검토" };
  const ACTION = {
    "고위험": "발송 차단·보고 — 발송을 멈추고 노출된 번호를 개인정보보호 책임자에게 보고합니다.",
    "중위험": "마스킹 요청 — 노출된 항목을 가린 뒤 다시 제출하도록 요청합니다.",
    "저위험": "발송 승인 기록 — 노출 항목이 없어 발송 가능으로 기록합니다.",
    "검토 필요": "담당자 확인 요청 — 판독할 수 없거나 재식별 위험이 있어 담당자가 원본을 직접 확인합니다.",
  };
  const KEY_STORE = "yomi_upstage_key";

  // 키 기억(세션 한정)
  try {
    const k = sessionStorage.getItem(KEY_STORE);
    if (k) { $("apikey").value = k; $("remember").checked = true; }
  } catch (e) {}

  // 샘플 목록
  (window.CASES || []).forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id;
    o.textContent = `${c.set} · ${c.docs.join(", ")} (정답 ${c.risk_level})`;
    $("sample").appendChild(o);
  });
  $("file").addEventListener("change", () => { if ($("file").files.length) $("sample").value = ""; });

  function step(name, st) {
    document.querySelectorAll("#aiSteps li").forEach((li) => {
      if (name === null) li.removeAttribute("data-st");
      else if (li.dataset.s === name) li.setAttribute("data-st", st);
    });
  }

  async function apiError(res) {
    let msg = "";
    try { const j = await res.json(); msg = j.error?.message || j.message || JSON.stringify(j); } catch (e) { msg = await res.text().catch(() => ""); }
    if (res.status === 401) msg = "API 키가 올바르지 않습니다. " + msg;
    if (res.status === 429) msg = "요청 한도를 넘었습니다. 잠시 뒤 다시 시도하세요. " + msg;
    return new Error(`HTTP ${res.status}: ${msg}`);
  }

  async function parseDoc(key, blob, name) {
    const fd = new FormData();
    fd.append("document", blob, name);
    fd.append("model", "document-parse");
    fd.append("ocr", "force");
    fd.append("output_formats", '["text"]');
    const res = await fetch(`${API}/document-digitization`, { method: "POST", headers: { Authorization: `Bearer ${key}` }, body: fd });
    if (!res.ok) throw await apiError(res);
    const j = await res.json();
    const pages = {};
    (j.elements || []).forEach((e) => {
      const t = e.content?.text || "";
      if (!t.trim()) return;
      (pages[e.page] ??= []).push(t);
    });
    const keys = Object.keys(pages).map(Number).sort((a, b) => a - b);
    let text = keys.map((p) => `[${p}쪽]\n${pages[p].join("\n")}`).join("\n\n");
    if (!text.trim()) text = j.content?.text || "";
    return { text, pages: j.usage?.pages ?? keys.length };
  }

  function pickJson(s) {
    s = s.replace(/```(?:json)?/g, "").trim();
    const a = s.indexOf("{"), b = s.lastIndexOf("}");
    if (a < 0 || b < 0) throw new Error("판정 결과에서 JSON을 찾지 못했습니다.");
    return JSON.parse(s.slice(a, b + 1));
  }

  async function judge(key, model, text) {
    const body = {
      model,
      temperature: 0,
      max_tokens: 6000,
      messages: [
        { role: "system", content: window.JUDGE_SYSTEM },
        { role: "user", content: "다음은 발송할 서류 묶음 1건의 OCR 텍스트다.\n\n" + (text.trim() || "(읽힌 글자 없음)") },
      ],
    };
    const res = await fetch(`${API}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await apiError(res);
    const j = await res.json();
    const raw = j.choices?.[0]?.message?.content || "";
    return { raw, out: pickJson(raw) };
  }

  const norm = (a) => [...new Set((a || []).map((x) => String(x).trim()))].sort().join(",");

  function show(out, parsed, raw, kase) {
    const lvl = out.risk_level || "?";
    const items = Array.isArray(out.detected_items) ? out.detected_items : [];
    let h = `<span class="note">risk_level</span><div class="lvl"><span class="badge ${BADGE[lvl] || ""}" style="font-size:24px;padding:4px 16px">${esc(lvl)}</span></div>`;
    h += `<p><b>후속 조치:</b> ${esc(ACTION[lvl] || "-")}</p>`;
    h += `<p><b>detected_items:</b> ${items.length ? esc(items.join(", ")) : "없음"}<br><b>data_subject:</b> ${esc(out.data_subject || "-")}</p>`;
    h += `<p><b>reason:</b> ${esc(out.reason || "")}</p>`;
    if (kase) {
      const a = kase;
      const ok1 = a.risk_level === lvl, ok2 = norm(a.detected_items) === norm(items), ok3 = a.data_subject === out.data_subject;
      const mark = (b) => (b ? "✅" : "❌");
      h += `<div class="cmp"><b>정답 비교 (${esc(a.set)})</b><br>${mark(ok1)} 위험도: 정답 ${esc(a.risk_level)}<br>${mark(ok2)} 노출 항목: 정답 ${esc(a.detected_items.join(", ") || "없음")}<br>${mark(ok3)} 정보 주체: 정답 ${esc(a.data_subject)}<br><span class="note">${ok1 && ok2 && ok3 ? "세 키 모두 일치" : "일부 불일치 — 사이트 판정은 문서 분할·검증 노드 없이 한 번에 처리하므로 Studio 결과와 다를 수 있습니다."}</span></div>`;
    }
    const docs = Array.isArray(out.documents) ? out.documents : [];
    h += `<details><summary>문서별 추출 결과 (${docs.length})</summary><pre class="raw">${esc(JSON.stringify(docs, null, 2))}</pre></details>`;
    h += `<details><summary>OCR 텍스트 (${parsed.pages}쪽)</summary><pre class="raw">${esc(parsed.text)}</pre></details>`;
    h += `<details><summary>모델 원문 응답</summary><pre class="raw">${esc(raw)}</pre></details>`;
    $("aiOut").innerHTML = h;
  }

  $("aiRun").addEventListener("click", async () => {
    const key = $("apikey").value.trim();
    const model = $("model").value.trim() || "solar-pro2";
    const out = $("aiOut");
    try { if ($("remember").checked) sessionStorage.setItem(KEY_STORE, key); else sessionStorage.removeItem(KEY_STORE); } catch (e) {}
    if (!key) { out.innerHTML = '<p class="err">Upstage API 키를 입력하세요.</p>'; return; }
    const kase = (window.CASES || []).find((c) => c.id === $("sample").value);
    let blob, name;
    if (kase) {
      const r = await fetch(kase.file).catch(() => null);
      if (!r || !r.ok) { out.innerHTML = '<p class="err">샘플 파일을 불러오지 못했습니다. 사이트를 웹 주소(GitHub Pages)로 열었는지 확인하세요.</p>'; return; }
      blob = await r.blob(); name = kase.set + ".pdf";
    } else if ($("file").files.length) {
      blob = $("file").files[0]; name = blob.name;
      if (blob.size > 50 * 1024 * 1024) { out.innerHTML = '<p class="err">50MB 이하 파일만 올릴 수 있습니다.</p>'; return; }
    } else { out.innerHTML = '<p class="err">샘플을 고르거나 파일을 올리세요.</p>'; return; }

    $("aiRun").disabled = true; step(null);
    out.innerHTML = `<span class="note">${esc(name)} 판정 중… 보통 20~60초 걸립니다.</span>`;
    let parsed;
    try {
      step("parse", "run");
      parsed = await parseDoc(key, blob, name);
      step("parse", "ok");
      step("judge", "run");
      const { raw, out: res } = await judge(key, model, parsed.text);
      step("judge", "ok");
      show(res, parsed, raw, kase);
    } catch (e) {
      document.querySelectorAll('#aiSteps li[data-st="run"]').forEach((li) => li.setAttribute("data-st", "err"));
      out.innerHTML = `<p class="err">판정하지 못했습니다.</p><pre class="raw">${esc(e.message || e)}</pre>` +
        (parsed ? `<details><summary>OCR 텍스트</summary><pre class="raw">${esc(parsed.text)}</pre></details>` : "");
    } finally { $("aiRun").disabled = false; }
  });
})();
