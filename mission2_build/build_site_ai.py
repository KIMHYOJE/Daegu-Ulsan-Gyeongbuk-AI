# -*- coding: utf-8 -*-
"""소개 사이트(docs/)의 AI 판정용 프롬프트와 샘플 파일을 최종 workflow.json·answer.json에서 만든다.
Studio 워크플로우와 같은 추출 항목 설명·판정 규칙을 쓰도록 한 곳에서 생성한다."""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "최종제출_제출물"
DOCS = ROOT / "docs"
w = json.loads((FINAL / "요미의 코딩_최종제출_workflow.json").read_text(encoding="utf-8"))
cfg = w["workflowConfig"]

# 1) 추출 항목 설명 (Studio Extract 노드와 동일)
props = cfg["informationExtractConfiguration"]["schemas"][0]["json_schema"]["schema"]["properties"]
lines = []
for k, v in props.items():
    desc = v.get("description") or v.get("items", {}).get("description", "")
    typ = "문자열 목록" if v.get("type") == "array" else ("true/false" if v.get("type") == "boolean" else "문자열")
    lines.append(f"- {k} ({typ}): {desc}")
extract_spec = "\n".join(lines)
extract_guide = cfg["informationExtractConfiguration"]["schemas"][0].get("userSystemPrompt", "")

# 2) 판정 규칙 (Studio 위험도_판정 노드와 동일, 출력 형식만 JSON으로 바꿈)
judge = cfg["instructConfiguration"]["nodes"][0]["prompt"]
cut = judge.index("[출력]")
judge_rules = judge[:cut].strip()

system = f"""{judge_rules}

[입력] 사용자 메시지에 Upstage Document Parse(OCR)로 읽은 서류 묶음의 텍스트가 쪽 순서대로 들어 있다.
먼저 서식(문서)마다 아래 항목을 추출한 뒤, 위 규칙으로 묶음 전체의 위험도를 판정한다.
{extract_guide}
OCR 텍스트가 거의 비어 있거나 번호·이름 칸이 깨진 글자로만 읽혔으면 그 문서의 readability를 'unclear'로 적는다.

[문서별 추출 항목]
{extract_spec}

[출력] 설명 없이 JSON 객체 하나만 출력한다. 마크다운 코드 블록을 쓰지 않는다.
{{"documents": [{{"document_title": "...", "readability": "clear", "masking_stamp": false, "resident_reg_numbers": [], "...": "위 항목 전부"}}],
 "risk_level": "고위험 | 중위험 | 저위험 | 검토 필요 중 하나",
 "detected_items": ["정해진 12개 이름 중 노출된 것"],
 "data_subject": "개인 | 기업 | 개인·기업 | 없음",
 "reason": "판정 근거 1~2문장. 어떤 문서의 어떤 값이 노출·마스킹·판독 불가인지 실제 값을 인용"}}"""

follow = {}
for n in cfg["instructConfiguration"]["nodes"][1:]:
    follow[n.get("name") or n.get("nodeName") or str(len(follow))] = n.get("prompt", "")[:200]

(ROOT / "api" / "_prompt.js").write_text(
    "// mission2_build/build_site_ai.py 로 생성. Studio 설정 #9와 같은 규칙.\n"
    "export const JUDGE_SYSTEM = " + json.dumps(system, ensure_ascii=False) + ";\n",
    encoding="utf-8")
(DOCS / "prompt.js").unlink(missing_ok=True)

# 3) 샘플 PDF와 정답
sd = DOCS / "samples"
sd.mkdir(exist_ok=True)
ans = json.loads((FINAL / "요미의 코딩_최종제출_answer.json").read_text(encoding="utf-8"))
cases = []
for c in ans["cases"]:
    src = FINAL / c["file"]
    name = src.name.split("_")[-1]  # set01.pdf
    shutil.copyfile(src, sd / name)
    cases.append({"id": c["case_id"], "set": name.replace(".pdf", ""), "file": f"samples/{name}",
                  "docs": c["documents"], **c["answer"]})
(DOCS / "cases.js").write_text("window.CASES=" + json.dumps(cases, ensure_ascii=False) + ";\n", encoding="utf-8")
print("prompt chars", len(system), "| samples", len(cases))
