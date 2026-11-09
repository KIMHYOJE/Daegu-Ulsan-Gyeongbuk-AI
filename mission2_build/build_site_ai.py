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

# 2) 사이트 판정 함수용: 추출 지시문과 추출 스키마 (판정 규칙은 api/grade.js 코드에 Studio 위험도_판정 규칙과 같게 구현)
extract_system = f"""당신은 은행 개인정보보호 담당자의 1차 점검 보조자다. 사용자 메시지에 Upstage Document Parse(OCR)로 읽은 서류 묶음의 텍스트가 쪽 순서대로 들어 있다.
묶음 안의 서식(문서)마다 documents 배열에 하나씩, 아래 항목을 칸별로 추출한다. 판정은 하지 않는다.
{extract_guide}
OCR 텍스트가 거의 비어 있거나, 서식 제목·이름·번호 칸이 깨진 글자나 뜻 없는 문자로만 읽혔으면 그 문서의 readability를 'unclear'로 적고, 읽지 못한 값은 만들지 않는다.

[문서별 추출 항목]
{extract_spec}"""
schema = {"type": "object", "additionalProperties": False, "required": ["documents"],
          "properties": {"documents": {"type": "array", "items": {
              "type": "object", "additionalProperties": False, "required": list(props.keys()),
              "properties": {k: ({"type": "array", "items": {"type": "string"}} if v.get("type") == "array"
                                 else {"type": v.get("type", "string")}) for k, v in props.items()}}}}}
(ROOT / "api" / "_prompt.js").write_text(
    "// mission2_build/build_site_ai.py 로 생성. Studio 설정의 Extract 노드와 같은 항목 설명.\n"
    "export const EXTRACT_SYSTEM = " + json.dumps(extract_system, ensure_ascii=False) + ";\n"
    "export const EXTRACT_SCHEMA = " + json.dumps(schema, ensure_ascii=False) + ";\n",
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
print("prompt chars", len(extract_system), "| samples", len(cases))
