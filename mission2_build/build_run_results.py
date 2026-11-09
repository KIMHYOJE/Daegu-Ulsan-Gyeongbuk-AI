# -*- coding: utf-8 -*-
"""최종 제출물 04 '실행 결과'를 만든다.
Upstage Studio 에이전트 '요미의 코딩'(최종 설정)이 14개 서류 묶음을 돌린 '위험도_판정' 노드 출력
(studio_results/studio_instruct_raw.json, 2026-11-09 Studio에서 수집)을 정답지와 같은 출력 키 4개로 정리한다."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "최종제출_제출물"
raw = json.loads((ROOT / "mission2_build/studio_results/studio_instruct_raw.json").read_text(encoding="utf-8"))
ans = json.loads((FINAL / "요미의 코딩_최종제출_answer.json").read_text(encoding="utf-8"))
KEYS = ans["output_keys"]

def parse(content):
    t = re.sub(r"【†\d+】", "", content)
    out = {}
    for k in KEYS:
        m = re.search(rf"^{k}:\s*(.*?)(?=^\w+:|\Z)", t, re.S | re.M)
        out[k] = (m.group(1).strip() if m else "")
    items = out["detected_items"].strip().strip("[]")
    out["detected_items"] = [x.strip().strip("'\"") for x in items.split(",") if x.strip()]
    out["reason"] = re.sub(r"\s+", " ", out["reason"].replace("`", "")).strip()
    return out

cases, ok = [], 0
for c in ans["cases"]:
    s = re.search(r"set\d\d", c["file"]).group(0)
    r = raw[s]
    o = parse(r["content"])
    a = c["answer"]
    m = {"risk_level": o["risk_level"] == a["risk_level"],
         "detected_items": sorted(o["detected_items"]) == sorted(a["detected_items"]),
         "data_subject": o["data_subject"] == a["data_subject"]}
    ok += all(m.values())
    cases.append({"case_id": c["case_id"], "file": c["file"], "documents": c["documents"],
                  "workflow_run_id": r["run"], "run_at": r["at"],
                  "output": {k: o[k] for k in KEYS},
                  "match_answer": m})

result = {
    "task": ans["task"],
    "workflow": "Upstage Studio 에이전트 '요미의 코딩' (요미의 코딩_최종제출_workflow.json과 같은 설정)",
    "source": "Studio 실행 기록의 '위험도_판정' 노드 출력 원문에서 인용 표시【†n】만 지우고 옮김",
    "unit": ans["unit"],
    "output_keys": KEYS,
    "decision_values": ans["decision_values"],
    "summary": {"cases": len(cases), "all_keys_match": ok,
                "note": "match_answer는 risk_level·detected_items·data_subject를 정답지와 비교한 값 (reason은 서술형이라 비교 제외)"},
    "cases": cases,
}
out = FINAL / "요미의 코딩_최종제출_실행결과.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(out.name, "| cases", len(cases), "| match", ok, "/", len(cases))
for c in cases:
    if not all(c["match_answer"].values()): print("MISMATCH", c["file"], c["output"])
    if not c["output"]["reason"]: print("NO REASON", c["file"])
