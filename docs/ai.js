// AI 판정: 파일을 Cloudflare Worker(GRADER_URL)로 보내면 Worker가 Upstage Document Parse(OCR) → Solar 판정을 수행한다.
// Upstage 키는 Worker 비밀값에만 있다.
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
  const GRADER = (window.GRADER_URL || "").replace(/\/$/, "");

  (window.CASES || []).forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id;
    o.textContent = `${c.set} · ${c.docs.join(", ")} (정답 ${c.risk_level})`;
    $("sample").appendChild(o);
  });
  if (window.CASES && window.CASES.length) $("sample").value = window.CASES[0].id;
  $("file").addEventListener("change", () => { if ($("file").files.length) $("sample").value = ""; });

  const setStep = (st) => document.querySelectorAll("#aiSteps li").forEach((li) => (st ? li.setAttribute("data-st", st) : li.removeAttribute("data-st")));
  const norm = (a) => [...new Set((a || []).map((x) => String(x).trim()))].sort().join(",");

  function show(out, ocr, raw, kase) {
    const lvl = out.risk_level || "?";
    const items = Array.isArray(out.detected_items) ? out.detected_items : [];
    let h = `<span class="note">risk_level</span><div class="lvl"><span class="badge ${BADGE[lvl] || ""}" style="font-size:24px;padding:4px 16px">${esc(lvl)}</span></div>`;
    h += `<p><b>후속 조치:</b> ${esc(ACTION[lvl] || "-")}</p>`;
    h += `<p><b>detected_items:</b> ${items.length ? esc(items.join(", ")) : "없음"}<br><b>data_subject:</b> ${esc(out.data_subject || "-")}</p>`;
    h += `<p><b>reason:</b> ${esc(out.reason || "")}</p>`;
    if (kase) {
      const ok1 = kase.risk_level === lvl, ok2 = norm(kase.detected_items) === norm(items), ok3 = kase.data_subject === out.data_subject;
      const m = (b) => (b ? "✅" : "❌");
      h += `<div class="cmp"><b>정답 비교 (${esc(kase.set)})</b><br>${m(ok1)} 위험도: 정답 ${esc(kase.risk_level)}<br>${m(ok2)} 노출 항목: 정답 ${esc(kase.detected_items.join(", ") || "없음")}<br>${m(ok3)} 정보 주체: 정답 ${esc(kase.data_subject)}<br><span class="note">${ok1 && ok2 && ok3 ? "세 키 모두 일치" : "일부 불일치 — 사이트는 문서 분할·검증 노드 없이 한 번에 판정하므로 Studio 결과(14/14)와 다를 수 있습니다."}</span></div>`;
    }
    const docs = Array.isArray(out.documents) ? out.documents : [];
    h += `<details><summary>문서별 추출 결과 (${docs.length})</summary><pre class="raw">${esc(JSON.stringify(docs, null, 2))}</pre></details>`;
    if (ocr) h += `<details><summary>OCR 텍스트 (${esc(ocr.pages)}쪽)</summary><pre class="raw">${esc(ocr.text)}</pre></details>`;
    h += `<details><summary>모델 원문 응답</summary><pre class="raw">${esc(raw)}</pre></details>`;
    $("aiOut").innerHTML = h;
  }

  $("aiRun").addEventListener("click", async () => {
    const out = $("aiOut");
    if (!GRADER) { out.innerHTML = '<p class="err">AI 판정 서버 주소가 설정되지 않았습니다.</p>'; return; }
    const kase = (window.CASES || []).find((c) => c.id === $("sample").value);
    let blob, name;
    if (kase) {
      const r = await fetch(kase.file).catch(() => null);
      if (!r || !r.ok) { out.innerHTML = '<p class="err">샘플 파일을 불러오지 못했습니다.</p>'; return; }
      blob = await r.blob(); name = kase.set + ".pdf";
    } else if ($("file").files.length) {
      blob = $("file").files[0]; name = blob.name;
      if (blob.size > 10 * 1024 * 1024) { out.innerHTML = '<p class="err">10MB 이하 파일만 판정할 수 있습니다.</p>'; return; }
    } else { out.innerHTML = '<p class="err">샘플을 고르거나 파일을 올리세요.</p>'; return; }

    $("aiRun").disabled = true; setStep("run");
    out.innerHTML = `<span class="note">${esc(name)} 판정 중… 보통 20~60초 걸립니다.</span>`;
    try {
      const fd = new FormData();
      fd.append("document", blob, name);
      const res = await fetch(`${GRADER}/grade`, { method: "POST", body: fd });
      let j = {};
      try { j = await res.json(); } catch (e) {}
      if (!res.ok || !j.result) throw Object.assign(new Error(j.error || `서버 오류 (HTTP ${res.status})`), { ocr: j.ocr });
      setStep("ok");
      show(j.result, j.ocr, j.raw || "", kase);
    } catch (e) {
      setStep("err");
      out.innerHTML = `<p class="err">판정하지 못했습니다: ${esc(e.message === "Failed to fetch" ? "판정 서버에 연결하지 못했습니다." : e.message)}</p>` +
        (e.ocr ? `<details><summary>OCR 텍스트</summary><pre class="raw">${esc(e.ocr.text)}</pre></details>` : "");
    } finally { $("aiRun").disabled = false; }
  });
})();
