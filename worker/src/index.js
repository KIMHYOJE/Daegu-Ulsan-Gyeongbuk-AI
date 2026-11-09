// 민감정보 위험도 판정 중계 Worker
// 사이트(GitHub Pages)에서 파일을 받아 Upstage Document Parse(OCR) → Solar 판정을 서버에서 수행한다.
// Upstage 키는 Cloudflare 비밀값 UPSTAGE_API_KEY에만 있고 브라우저로 나가지 않는다.
import { JUDGE_SYSTEM } from "./prompt.js";

const API = "https://api.upstage.ai/v1";
const MAX_BYTES = 10 * 1024 * 1024; // 10MB
const MODEL = "solar-pro2";

function allowedOrigin(origin, env) {
  const list = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
  if (!origin) return null;
  if (list.includes(origin)) return origin;
  if (/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return origin;
  return null;
}

function json(body, status, origin) {
  const h = { "Content-Type": "application/json; charset=utf-8" };
  if (origin) Object.assign(h, { "Access-Control-Allow-Origin": origin, Vary: "Origin" });
  return new Response(JSON.stringify(body), { status, headers: h });
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

async function parseDoc(env, file) {
  const fd = new FormData();
  fd.append("document", file, file.name || "document.pdf");
  fd.append("model", "document-parse");
  fd.append("ocr", "force");
  fd.append("output_formats", '["text"]');
  const res = await fetch(`${API}/document-digitization`, {
    method: "POST", headers: { Authorization: `Bearer ${env.UPSTAGE_API_KEY}` }, body: fd,
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

async function judge(env, text) {
  const res = await fetch(`${API}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.UPSTAGE_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: env.MODEL || MODEL,
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

export default {
  async fetch(request, env) {
    const origin = allowedOrigin(request.headers.get("Origin"), env);
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      if (!origin) return new Response(null, { status: 403 });
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": origin,
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400",
          Vary: "Origin",
        },
      });
    }
    if (url.pathname === "/health") return json({ ok: true, keySet: Boolean(env.UPSTAGE_API_KEY) }, 200, origin);
    if (url.pathname !== "/grade" || request.method !== "POST") return json({ error: "POST /grade 만 지원합니다." }, 404, origin);
    if (!origin) return json({ error: "허용되지 않은 사이트에서 온 요청입니다." }, 403, null);
    if (!env.UPSTAGE_API_KEY) return json({ error: "서버에 Upstage 키가 설정되지 않았습니다." }, 500, origin);

    if (env.LIMITER) {
      const ip = request.headers.get("CF-Connecting-IP") || "unknown";
      const { success } = await env.LIMITER.limit({ key: ip });
      if (!success) return json({ error: "요청이 너무 많습니다. 1분 뒤 다시 시도하세요." }, 429, origin);
    }

    let file;
    try {
      const form = await request.formData();
      file = form.get("document");
    } catch (e) {
      return json({ error: "파일을 읽지 못했습니다." }, 400, origin);
    }
    if (!file || typeof file === "string") return json({ error: "document 파일이 없습니다." }, 400, origin);
    if (file.size > MAX_BYTES) return json({ error: "10MB 이하 파일만 판정할 수 있습니다." }, 413, origin);

    let parsed;
    try {
      parsed = await parseDoc(env, file);
      const { raw, result } = await judge(env, parsed.text);
      return json({ result, raw, ocr: parsed }, 200, origin);
    } catch (e) {
      return json({ error: String(e.message || e), ocr: parsed || null }, 502, origin);
    }
  },
};
