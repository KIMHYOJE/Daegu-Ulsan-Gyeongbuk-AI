// 민감정보 위험도 판정 함수 (Vercel Functions, POST /api/grade · GET /api/grade 는 상태 확인)
// 1) Upstage Document Parse(OCR)로 글자를 읽고
// 2) Solar가 서식마다 18개 항목을 칸별로 추출(Studio Extract 노드와 같은 항목 설명, JSON 스키마 고정)한 뒤
// 3) 위험도·노출 항목·정보 주체는 Studio 위험도_판정 규칙을 그대로 옮긴 코드가 정한다(같은 입력이면 늘 같은 판정).
// Upstage 키는 Vercel 환경변수 UPSTAGE_API_KEY에만 있고 브라우저로 나가지 않는다.
import { EXTRACT_SYSTEM, EXTRACT_SCHEMA } from "./_prompt.js";

const API = "https://api.upstage.ai/v1";
export const MAX_BYTES = 4 * 1024 * 1024; // Vercel 요청 본문 한도(4.5MB) 안쪽
const MODEL = process.env.MODEL || "solar-pro4";
const LIMIT = 16, WINDOW_MS = 60_000; // IP당 1분에 16번 (인스턴스 단위, 샘플 14개 한꺼번에 판정 허용)
const hits = new Map();

export const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });

export function sameSite(request) {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  let host;
  try { host = new URL(origin).host; } catch (e) { return false; }
  const own = request.headers.get("x-forwarded-host") || request.headers.get("host");
  return host === own || /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host);
}

export function limited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  if (list.length >= LIMIT) { hits.set(ip, list); return true; }
  list.push(now); hits.set(ip, list);
  if (hits.size > 5000) hits.clear();
  return false;
}

async function upstageError(res, step) {
  let msg = "";
  try { const j = await res.json(); msg = j.error?.message || j.message || ""; } catch (e) {}
  return new Error(`${step} 실패 (HTTP ${res.status}) ${msg}`.trim());
}

async function parseDoc(key, file) {
  const fd = new FormData();
  fd.append("document", file, file.name || "document.pdf");
  fd.append("model", "document-parse");
  fd.append("ocr", "force");
  fd.append("output_formats", '["text"]');
  const res = await fetch(`${API}/document-digitization`, {
    method: "POST", headers: { Authorization: `Bearer ${key}` }, body: fd,
  });
  if (!res.ok) throw await upstageError(res, "문서 읽기");
  const j = await res.json();
  const pages = {};
  for (const e of j.elements || []) {
    const t = e.content?.text || "";
    if (t.trim()) (pages[e.page] ??= []).push(t);
  }
  const keys = Object.keys(pages).map(Number).sort((a, b) => a - b);
  let text = keys.map((p) => `[${p}쪽]\n${pages[p].join("\n")}`).join("\n\n");
  if (!text.trim()) text = j.content?.text || "";
  return { text, pages: j.usage?.pages ?? keys.length };
}

function pickJson(s) {
  s = String(s || "").replace(/```(?:json)?/g, "").trim();
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a < 0 || b < 0) throw new Error("추출 결과에서 JSON을 찾지 못했습니다.");
  return JSON.parse(s.slice(a, b + 1));
}

async function extract(key, text) {
  const body = {
    model: MODEL,
    temperature: 0,
    max_tokens: 8000,
    messages: [
      { role: "system", content: EXTRACT_SYSTEM },
      { role: "user", content: "다음은 발송할 서류 묶음 1건의 OCR 텍스트다. 서식마다 항목을 추출하라.\n\n" + (text.trim() || "(읽힌 글자 없음)") },
    ],
    response_format: { type: "json_schema", json_schema: { name: "documents", strict: true, schema: EXTRACT_SCHEMA } },
  };
  let res = await fetch(`${API}/chat/completions`, {
    method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (res.status === 400) { // 구조화 출력을 받지 않는 모델이면 일반 JSON 출력으로 다시 요청
    delete body.response_format;
    body.messages[0].content += "\n\n[출력] 설명 없이 {\"documents\": [...]} JSON 객체 하나만 출력한다.";
    res = await fetch(`${API}/chat/completions`, {
      method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
  }
  if (!res.ok) throw await upstageError(res, "항목 추출");
  const j = await res.json();
  const raw = j.choices?.[0]?.message?.content || "";
  const docs = pickJson(raw).documents;
  return { raw, documents: Array.isArray(docs) ? docs : [] };
}

// ---- 판정 규칙 (Studio 위험도_판정 노드와 같은 순서·기준) ----
const MASK = /[*X●○]/;
const HIGH = [["resident_reg_numbers", "주민등록번호"], ["foreigner_reg_numbers", "외국인등록번호"], ["passport_numbers", "여권번호"], ["driver_license_numbers", "운전면허번호"], ["card_numbers", "카드번호"]];
const MID = [["account_numbers", "계좌번호"], ["mobile_numbers", "휴대전화번호"], ["personal_addresses", "주소"], ["emails", "이메일"], ["income_values", "소득정보"], ["credit_values", "신용정보"], ["corporate_financials", "기업재무정보"]];
const ALL = [...HIGH, ...MID];
const PERSONAL = new Set(["주민등록번호", "외국인등록번호", "여권번호", "운전면허번호", "휴대전화번호", "주소", "이메일", "소득정보", "신용정보"]);
const arr = (v) => (Array.isArray(v) ? v.map((x) => String(x).trim()).filter(Boolean) : []);
const shown = (v) => arr(v).filter((x) => !MASK.test(x));   // 마스킹 문자가 하나도 없는 값만 노출
const masked = (v) => arr(v).filter((x) => MASK.test(x));
const titleOf = (d) => String(d.document_title || "").trim() || "제목 없는 서식";

function judge(documents) {
  // OCR이 글자를 하나도 못 읽어 서식이 없으면 '노출 없음'이 아니라 내용 판독 실패로 본다
  if (!documents.length) documents = [{ document_title: "", readability: "unclear" }];
  const docs = documents.map((d) => ({ ...d, title: titleOf(d) }));
  // 1단계 검토 필요
  const unreadable = docs.filter((d) => String(d.readability || "").trim().toLowerCase() === "unclear");
  const emptyRead = docs.filter((d) => {
    const t = String(d.document_title || "").trim();
    const noTitle = !t || /^document$/i.test(t);
    return noTitle && !arr(d.person_names).length && ALL.every(([k]) => !arr(d[k]).length);
  });
  const reid = docs.filter((d) => {
    const names = arr(d.person_names);
    if (!names.length || names.some((n) => !MASK.test(n))) return false;
    const q = arr(d.quasi_identifiers).join(" ");
    return /(19|20)\d{2}|\d+\s*세|년생/.test(q) && /\(주\)|㈜|주식회사|회사|은행|그룹/.test(q) && /부|팀|과장|대리|사원|차장|부장|주임|이사|연구원|직위|직급/.test(q);
  });

  // 노출 항목 (판독 가능한 문서 기준)
  const usable = docs.filter((d) => !unreadable.includes(d) && !emptyRead.includes(d));
  const found = [];  // {item, values, doc, owner}
  for (const [k, item] of ALL) {
    for (const d of usable) {
      const v = shown(d[k]);
      if (v.length) found.push({ item, values: v, doc: d.title, corp: String(d.owner_type || "").includes("기업") });
    }
  }
  const items = [...new Set(found.map((f) => f.item))];
  const isHigh = items.some((i) => HIGH.some(([, n]) => n === i));

  let risk;
  if (unreadable.length || emptyRead.length || reid.length) risk = "검토 필요";
  else if (isHigh) risk = "고위험";
  else if (items.length) risk = "중위험";
  else risk = "저위험";

  // 정보 주체
  let personal = false, corporate = false;
  for (const f of found) {
    if (PERSONAL.has(f.item)) personal = true;
    else if (f.item === "기업재무정보") corporate = true;
    else if (f.corp) corporate = true; else personal = true; // 계좌·카드: 법인 서류면 기업
  }
  const subject = !items.length ? "없음" : personal && corporate ? "개인·기업" : personal ? "개인" : "기업";
  const detected = risk === "검토 필요" ? items : items;

  // 판정 근거 (실제 값 인용)
  // 서식별로 묶어 "서식: 항목 값, 항목 값" 형태로 인용
  const quoteAll = (list) => {
    const by = new Map();
    for (const f of list) (by.get(f.doc) || by.set(f.doc, []).get(f.doc)).push(`${f.item} ${f.values.slice(0, 2).join(", ")}${f.values.length > 2 ? " 외" : ""}`);
    return [...by].map(([doc, xs]) => `[${doc}] ${xs.slice(0, 3).join(" · ")}`).join(" / ");
  };
  let reason;
  if (risk === "검토 필요") {
    const why = [];
    if (unreadable.length) why.push(`${unreadable.map((d) => d.title).join(", ")}은(는) 흐리거나 번호·이름 칸을 읽을 수 없어 노출 여부를 확인할 수 없음`);
    if (emptyRead.length) why.push(`서식 제목과 번호·이름 칸이 하나도 읽히지 않은 문서가 있어 '노출 없음'으로 볼 수 없음`);
    if (reid.length) why.push(`${reid.map((d) => d.title).join(", ")}에서 이름은 가렸지만 회사·직위·출생연도가 함께 남아 누구인지 짐작할 수 있음(재식별 위험)`);
    reason = why.join(". ") + (found.length ? `. 그 밖에 읽힌 문서에서 가려지지 않은 값: ${quoteAll(found)}.` : ".");
  } else if (found.length) {
    const top = [...found].sort((a, b) => (HIGH.some(([, n]) => n === b.item) ? 1 : 0) - (HIGH.some(([, n]) => n === a.item) ? 1 : 0));
    reason = `가려지지 않은 값: ${quoteAll(top)}. ${isHigh ? "고위험 항목(주민·외국인등록·여권·운전면허·카드번호)이 노출되어 고위험" : "고위험 항목은 없고 중위험 항목이 노출되어 중위험"}.`;
    const hidden = usable.flatMap((d) => ALL.flatMap(([k, item]) => masked(d[k]).slice(0, 1).map((v) => `${item} ${v}`))).slice(0, 2);
    if (hidden.length) reason += ` ${hidden.join(", ")}처럼 가린 값은 노출로 세지 않음.`;
  } else {
    const hidden = usable.flatMap((d) => ALL.flatMap(([k, item]) => masked(d[k]).slice(0, 1).map((v) => `${item} ${v}`))).slice(0, 2);
    reason = hidden.length ? `민감정보가 모두 가려져 있음(${hidden.join(", ")}). 사업장 주소·사업자등록번호 같은 공개 정보는 제외.` : "가려지지 않은 민감정보가 없음. 사업장 주소·사업자등록번호 같은 공개 정보는 제외.";
  }
  // 화면에 보여 줄 근거: 서식별 노출 값·가린 값과 단계별 확인 결과
  const tierOf = (item) => (HIGH.some(([, n]) => n === item) ? "고위험" : "중위험");
  const evidence = {
    checks: {
      unreadable: unreadable.map((d) => d.title),
      empty_read: emptyRead.map((d) => d.title),
      reidentify: reid.map((d) => ({ doc: d.title, names: arr(d.person_names), clues: arr(d.quasi_identifiers) })),
    },
    documents: docs.map((d) => ({
      title: d.title,
      owner_type: d.owner_type || "",
      readability: d.readability || "",
      masking_stamp: Boolean(d.masking_stamp),
      skipped: unreadable.includes(d) ? "판독 불가" : emptyRead.includes(d) ? "내용 판독 실패" : "",
      items: ALL.map(([k, item]) => ({ item, tier: tierOf(item), exposed: shown(d[k]), masked: masked(d[k]) }))
        .filter((x) => x.exposed.length || x.masked.length),
    })),
  };
  return { risk_level: risk, detected_items: detected, data_subject: subject, reason, evidence };
}

export function GET() {
  return json({ ok: true, keySet: Boolean(process.env.UPSTAGE_API_KEY), model: MODEL });
}

export async function POST(request) {
  if (!sameSite(request)) return json({ error: "허용되지 않은 사이트에서 온 요청입니다." }, 403);
  const key = process.env.UPSTAGE_API_KEY;
  if (!key) return json({ error: "서버에 Upstage 키가 설정되지 않았습니다." }, 500);

  const ip = (request.headers.get("x-forwarded-for") || "unknown").split(",")[0].trim();
  if (limited(ip)) return json({ error: "요청이 너무 많습니다. 1분 뒤 다시 시도하세요." }, 429);

  let file;
  try {
    file = (await request.formData()).get("document");
  } catch (e) {
    return json({ error: "파일을 읽지 못했습니다." }, 400);
  }
  if (!file || typeof file === "string") return json({ error: "document 파일이 없습니다." }, 400);
  if (file.size > MAX_BYTES) return json({ error: "4MB 이하 파일만 판정할 수 있습니다." }, 413);

  let parsed;
  try {
    parsed = await parseDoc(key, file);
    const { raw, documents } = parsed.text.trim() ? await extract(key, parsed.text) : { raw: "", documents: [] };
    const result = { ...judge(documents), documents };
    return json({ result, raw, ocr: parsed });
  } catch (e) {
    return json({ error: String(e.message || e), ocr: parsed || null }, 502);
  }
}

export { judge };
