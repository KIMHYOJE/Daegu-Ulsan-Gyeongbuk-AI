// 가린 PDF용 좌표 찾기 (POST /api/mask)
// 판정에서 나온 '가려지지 않은 값' 목록을 받아, Upstage Document OCR의 단어 위치에서 그 값이 있는 자리를 찾아
// 쪽마다 가릴 상자(쪽 크기 대비 0~1 비율)를 돌려준다. 실제로 검게 칠하고 PDF로 묶는 일은 브라우저가 한다.
import { sameSite, limited, json, MAX_BYTES } from "./grade.js";

const API = "https://api.upstage.ai/v1";
const norm = (s) => String(s || "").toLowerCase().replace(/[^0-9a-z가-힣@]/g, "");

async function ocrWords(key, file) {
  const fd = new FormData();
  fd.append("document", file, file.name || "document.pdf");
  fd.append("model", "ocr");
  const res = await fetch(`${API}/document-digitization`, {
    method: "POST", headers: { Authorization: `Bearer ${key}` }, body: fd,
  });
  if (!res.ok) {
    let msg = "";
    try { const j = await res.json(); msg = j.error?.message || j.message || ""; } catch (e) {}
    throw new Error(`글자 위치 읽기 실패 (HTTP ${res.status}) ${msg}`.trim());
  }
  return (await res.json()).pages || [];
}

// 쪽의 단어들을 이어 붙인 문자열에서 값(정규화)을 찾아, 걸치는 단어 번호를 모은다
function findWords(words, value) {
  const parts = [], owner = [];
  words.forEach((w, i) => { for (const ch of norm(w.text)) { parts.push(ch); owner.push(i); } });
  const hay = parts.join(""), hit = new Set();
  const mark = (needle) => {
    if (!needle) return false;
    let found = false, at = hay.indexOf(needle);
    while (at >= 0) { for (let k = at; k < at + needle.length; k++) hit.add(owner[k]); found = true; at = hay.indexOf(needle, at + 1); }
    return found;
  };
  // '급여 48,000,000'처럼 항목 이름 + 숫자로 뽑힌 값은 숫자만 가린다 (서식 칸 이름은 남김)
  const labeled = String(value).match(/^[가-힣A-Za-z()·\s]+?\s*([\d][\d,.\-\s]*\d)\s*원?$/);
  if (labeled && norm(labeled[1]).length >= 4 && mark(norm(labeled[1]))) return hit;
  if (!mark(norm(value))) {
    // OCR 차이로 전체가 안 맞으면 값 속 4자리 이상 숫자 덩어리라도 가린다 (더 가리는 쪽이 안전)
    for (const d of String(value).match(/\d{4,}/g) || []) mark(d);
  }
  return hit;
}

export async function POST(request) {
  if (!sameSite(request)) return json({ error: "허용되지 않은 사이트에서 온 요청입니다." }, 403);
  const key = process.env.UPSTAGE_API_KEY;
  if (!key) return json({ error: "서버에 Upstage 키가 설정되지 않았습니다." }, 500);
  const ip = (request.headers.get("x-forwarded-for") || "unknown").split(",")[0].trim();
  if (limited(ip)) return json({ error: "요청이 너무 많습니다. 1분 뒤 다시 시도하세요." }, 429);

  let file, values;
  try {
    const fd = await request.formData();
    file = fd.get("document");
    values = JSON.parse(fd.get("values") || "[]").map(String).filter((v) => norm(v).length >= 2).slice(0, 200);
  } catch (e) {
    return json({ error: "요청을 읽지 못했습니다." }, 400);
  }
  if (!file || typeof file === "string") return json({ error: "document 파일이 없습니다." }, 400);
  if (file.size > MAX_BYTES) return json({ error: "4MB 이하 파일만 가릴 수 있습니다." }, 413);

  try {
    const pages = await ocrWords(key, file);
    const missing = new Set(values);
    const out = pages.map((p, pi) => {
      const words = p.words || [], W = p.width || 1, H = p.height || 1, idx = new Set();
      for (const v of values) { const h = findWords(words, v); if (h.size) missing.delete(v); h.forEach((i) => idx.add(i)); }
      const boxes = [...idx].map((i) => {
        const vs = words[i].boundingBox?.vertices || [];
        const xs = vs.map((q) => q.x), ys = vs.map((q) => q.y);
        if (!xs.length) return null;
        return { x: Math.min(...xs) / W, y: Math.min(...ys) / H, w: (Math.max(...xs) - Math.min(...xs)) / W, h: (Math.max(...ys) - Math.min(...ys)) / H, text: words[i].text };
      }).filter(Boolean);
      return { page: pi + 1, boxes };
    });
    return json({ pages: out, missing: [...missing] });
  } catch (e) {
    return json({ error: String(e.message || e) }, 502);
  }
}
