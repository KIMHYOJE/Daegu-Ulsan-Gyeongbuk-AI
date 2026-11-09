// 민감정보 위험도 판정 함수 (Vercel Functions, POST /api/grade · GET /api/grade 는 상태 확인)
// 사이트에서 받은 파일을 Upstage Document Parse(OCR) → Solar 판정에 넘긴다.
// Upstage 키는 Vercel 환경변수 UPSTAGE_API_KEY에만 있고 브라우저로 나가지 않는다.
import { JUDGE_SYSTEM } from "./_prompt.js";

const API = "https://api.upstage.ai/v1";
const MAX_BYTES = 4 * 1024 * 1024; // Vercel 요청 본문 한도(4.5MB) 안쪽
const MODEL = process.env.MODEL || "solar-pro2";
const LIMIT = 5, WINDOW_MS = 60_000; // IP당 1분에 5번 (인스턴스 단위)
const hits = new Map();

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });

// 같은 사이트(또는 로컬)에서 온 요청만 받는다
function sameSite(request) {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  let host;
  try { host = new URL(origin).host; } catch (e) { return false; }
  const own = request.headers.get("x-forwarded-host") || request.headers.get("host");
  return host === own || /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host);
}

function limited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  if (list.length >= LIMIT) { hits.set(ip, list); return true; }
  list.push(now); hits.set(ip, list);
  if (hits.size > 5000) hits.clear();
  return false;
}

function pickJson(s) {
  s = s.replace(/```(?:json)?/g, "").trim();
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a < 0 || b < 0) throw new Error("판정 결과에서 JSON을 찾지 못했습니다.");
  return JSON.parse(s.slice(a, b + 1));
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

async function judge(key, text) {
  const res = await fetch(`${API}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: MODEL,
      temperature: 0,
      max_tokens: 6000,
      messages: [
        { role: "system", content: JUDGE_SYSTEM },
        { role: "user", content: "다음은 발송할 서류 묶음 1건의 OCR 텍스트다.\n\n" + (text.trim() || "(읽힌 글자 없음)") },
      ],
    }),
  });
  if (!res.ok) throw await upstageError(res, "판정");
  const j = await res.json();
  const raw = j.choices?.[0]?.message?.content || "";
  return { raw, result: pickJson(raw) };
}

export function GET() {
  return json({ ok: true, keySet: Boolean(process.env.UPSTAGE_API_KEY) });
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
    const { raw, result } = await judge(key, parsed.text);
    return json({ result, raw, ocr: parsed });
  } catch (e) {
    return json({ error: String(e.message || e), ocr: parsed || null }, 502);
  }
}
