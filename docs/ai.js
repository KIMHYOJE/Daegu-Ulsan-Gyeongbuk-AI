// AI 판정: 파일을 Vercel 함수(GRADER_URL=/api)로 보내면 함수가 Upstage Document Parse(OCR) → Solar 판정을 수행한다.
// Upstage 키는 Vercel 환경변수에만 있다.
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

  // 샘플 목록에는 정답을 넣지 않는다 (정답은 판정 뒤 결과와 함께 보여 줌)
  (window.CASES || []).forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id;
    o.textContent = `${c.set} · ${c.docs.join(", ")}`;
    $("sample").appendChild(o);
  });
  if (window.CASES && window.CASES.length) $("sample").value = window.CASES[0].id;
  $("file").addEventListener("change", () => { if ($("file").files.length) $("sample").value = ""; });

  const setStep = (st) => document.querySelectorAll("#aiSteps li").forEach((li) => (st ? li.setAttribute("data-st", st) : li.removeAttribute("data-st")));
  const norm = (a) => [...new Set((a || []).map((x) => String(x).trim()))].sort().join(",");

  function show(out, ocr, raw, kase) {
    const lvl = out.risk_level || "?";
    const items = Array.isArray(out.detected_items) ? out.detected_items : [];
    let h = `<span class="note">판정 결과</span><div class="lvl"><span class="badge ${BADGE[lvl] || ""}" style="font-size:24px;padding:4px 16px">${esc(lvl)}</span></div>`;
    h += `<p><b>담당자가 할 일:</b> ${esc(ACTION[lvl] || "-")}</p>`;
    h += `<p><b>가려지지 않은 항목:</b> ${items.length ? esc(items.join(", ")) : "없음"}<br><b>누구의 정보인가:</b> ${esc(out.data_subject || "-")}</p>`;
    h += `<p><b>판정 근거:</b> ${esc(out.reason || "")}</p>`;
    if (kase) {
      const ok1 = kase.risk_level === lvl, ok2 = norm(kase.detected_items) === norm(items), ok3 = kase.data_subject === out.data_subject;
      const m = (b) => (b ? "✅" : "❌");
      h += `<div class="cmp"><b>정답과 비교 (${esc(kase.set)})</b><br>${m(ok1)} 위험도: 정답 ${esc(kase.risk_level)}<br>${m(ok2)} 노출 항목: 정답 ${esc(kase.detected_items.join(", ") || "없음")}<br>${m(ok3)} 정보 주체: 정답 ${esc(kase.data_subject)}<br><span class="note">${ok1 && ok2 && ok3 ? "세 항목 모두 정답과 같습니다." : "일부가 정답과 다릅니다. 이 페이지는 서식 분리·검증 단계 없이 한 번에 판정하므로 Studio 워크플로우 결과(14/14)와 다를 수 있습니다."}</span></div>`;
    }
    const docs = Array.isArray(out.documents) ? out.documents : [];
    h += `<details><summary>서식별 추출 결과 보기 (${docs.length}개)</summary><pre class="raw">${esc(JSON.stringify(docs, null, 2))}</pre></details>`;
    if (ocr) h += `<details><summary>문서에서 읽은 글자 보기 (${esc(ocr.pages)}쪽)</summary><pre class="raw">${esc(ocr.text)}</pre></details>`;
    h += `<details><summary>모델 원문 응답 (개발자용)</summary><pre class="raw">${esc(raw)}</pre></details>`;
    $("aiOut").innerHTML = h;
  }

  // 실패하면 무엇이 문제인지와 다음에 할 일을 함께 보여 준다
  function guide(status, msg) {
    if (status === 429) return "1분 뒤에 다시 눌러 주세요. 판정은 1분에 5번까지 할 수 있습니다.";
    if (status === 413) return "4MB 이하 파일로 다시 올려 주세요. 쪽수를 줄이거나 해상도를 낮추면 됩니다.";
    if (status === 403) return "이 사이트 주소에서 직접 열어 사용해 주세요.";
    if (status === 400) return "PDF나 이미지 파일을 다시 골라 주세요.";
    if (status === 0) return "인터넷 연결을 확인한 뒤 다시 시도해 주세요. 계속 안 되면 아래 ‘판정 규칙 체험’에서 규칙만 먼저 확인할 수 있습니다.";
    if (/키가 설정/.test(msg)) return "운영 중인 판정 서버 설정 문제입니다. 잠시 뒤 다시 시도하거나 아래 ‘판정 규칙 체험’을 이용해 주세요.";
    return "잠시 뒤 다시 시도해 주세요. 같은 문제가 계속되면 다른 샘플로 먼저 확인해 보세요.";
  }
  function fail(status, msg, ocr) {
    setStep("err");
    $("aiOut").innerHTML = `<p class="err"><b>판정하지 못했습니다.</b> ${esc(msg)}</p><p><b>이렇게 해 보세요:</b> ${esc(guide(status, msg))}</p>` +
      `<div class="btns"><button type="button" id="aiRetry">다시 판정하기</button></div>` +
      (ocr && ocr.text ? `<details><summary>문서에서 읽은 글자 보기</summary><pre class="raw">${esc(ocr.text)}</pre></details>` : "");
    $("aiRetry").addEventListener("click", run);
  }

  async function run() {
    const out = $("aiOut");
    if (!GRADER) return fail(-1, "판정 서버 주소가 설정되지 않았습니다.");
    const kase = (window.CASES || []).find((c) => c.id === $("sample").value);
    let blob, name;
    if (kase) {
      const r = await fetch(kase.file).catch(() => null);
      if (!r || !r.ok) return fail(0, "샘플 파일을 불러오지 못했습니다.");
      blob = await r.blob(); name = kase.set + ".pdf";
    } else if ($("file").files.length) {
      blob = $("file").files[0]; name = blob.name;
      if (blob.size > 4 * 1024 * 1024) return fail(413, "파일이 4MB보다 큽니다.");
    } else {
      out.innerHTML = '<p class="err">판정할 서류가 없습니다.</p><p><b>이렇게 해 보세요:</b> 위 목록에서 샘플을 고르거나 PDF·사진 파일을 올려 주세요.</p>';
      return;
    }

    $("aiRun").disabled = true; setStep("run");
    out.innerHTML = `<span class="note">${esc(name)} 판정 중… 보통 20~60초 걸립니다. 창을 닫지 말고 기다려 주세요.</span>`;
    try {
      const fd = new FormData();
      fd.append("document", blob, name);
      let res;
      try { res = await fetch(`${GRADER}/grade`, { method: "POST", body: fd }); }
      catch (e) { return fail(0, "판정 서버에 연결하지 못했습니다."); }
      let j = {};
      try { j = await res.json(); } catch (e) {}
      if (!res.ok || !j.result) return fail(res.status, j.error || `서버 오류 (HTTP ${res.status})`, j.ocr);
      setStep("ok");
      show(j.result, j.ocr, j.raw || "", kase);
    } finally { $("aiRun").disabled = false; }
  }
  $("aiRun").addEventListener("click", run);
})();
