# -*- coding: utf-8 -*-
"""발표 자료(HTML → Edge 헤드리스로 PDF). 실행 결과는 studio_results/final_results.json에서 읽는다."""
import base64, html, json, subprocess, sys
from pathlib import Path
import fitz

TEAM = sys.argv[1] if len(sys.argv) > 1 else "팀명"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "최종제출_제출물"
DECK = ROOT / "deck"
DECK.mkdir(exist_ok=True)
ANS = json.loads((OUT / f"{TEAM}_최종제출_answer.json").read_text(encoding="utf-8"))
RES = json.loads((ROOT / "studio_results" / "final_results.json").read_text(encoding="utf-8"))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
e = html.escape


def img(setname, page=0, clip=None, dpi=110):
    d = fitz.open(OUT / f"{TEAM}_최종제출_{setname}.pdf")
    pg = d[page]
    r = pg.rect
    c = fitz.Rect(r.x0 + clip[0] * r.width, r.y0 + clip[1] * r.height, r.x0 + clip[2] * r.width, r.y0 + clip[3] * r.height) if clip else None
    png = pg.get_pixmap(dpi=dpi, clip=c).tobytes("png")
    return "data:image/png;base64," + base64.b64encode(png).decode()


cases = ANS["cases"]
ok = 0
rows = []
for c in cases:
    sid = c["file"].split("_")[-1][:-4]
    a, r = c["answer"], RES["results"][sid]
    same = a["risk_level"] == r["risk_level"] and sorted(a["detected_items"]) == sorted(r["detected_items"]) and a["data_subject"] == r["data_subject"]
    ok += same
    rows.append(f"<tr><td>{c['case_id']}</td><td class='doc'>{e(' + '.join(c['documents']))}</td><td>{e(a['risk_level'])}</td>"
                f"<td>{e(r['risk_level'])}</td><td class='{'y' if same else 'n'}'>{'일치' if same else '불일치'}</td></tr>")
dist = {}
for c in cases:
    dist[c["answer"]["risk_level"]] = dist.get(c["answer"]["risk_level"], 0) + 1

S = []  # slides
S.append(f"""<section class="title"><div class="kicker">IM뱅크 지정주제 · {e(TEAM)}</div>
<h1>금융 서류 외부 발송 전<br>민감정보 자동 식별과 위험도 등급화</h1>
<p class="sub">Upstage Studio 워크플로우 — 서류 묶음 1건을 넣으면 고위험 · 중위험 · 저위험 · 검토 필요 중 하나와 근거를 냅니다</p></section>""")

S.append("""<section><h2>1. 문제 정의 — 보내기 직전, 사람이 눈으로 확인하는 일</h2>
<div class="cols"><div><h3>지금 하는 일</h3><ul>
<li>대출 심사·제출 서류를 다른 기관이나 고객에게 보내기 전에 담당자가 쪽마다 번호를 찾아 가렸는지 확인</li>
<li>한 묶음에 <b>개인 서식과 법인 서식이 섞여</b> 옴: 원천징수영수증, 동의서, 재무제표, 주주 명세, 사업자등록증</li>
<li>번호가 <b>칸마다 한 글자씩</b> 나뉘어 적힌 법정 서식이 많아 훑어보면 놓침</li></ul></div>
<div><h3>실제로 새는 지점</h3><ul>
<li>신청자 칸은 가렸는데 <b>배우자 칸</b>은 그대로</li>
<li>'개인정보 마스킹 처리본' 표시만 믿고 남은 <b>급여 금액</b>을 놓침</li>
<li>법인 서류(주주 명세) 안의 <b>개인 주주 주민등록번호</b></li>
<li>휴대폰으로 찍은 흐린 사본 — 읽지 못한 것을 "없음"으로 처리</li></ul></div></div>
<p class="note">목표: 1차 점검을 자동으로 하고, 확실하지 않은 건은 추측하지 않고 담당자에게 넘긴다</p></section>""")

S.append("""<section><h2>2. 워크플로우 기획 — 사람이 하던 순서를 노드로 옮김</h2>
<div class="flow">
<div class="step"><b>서류 펼치기</b><span>Parse<br>OCR 강제</span></div><div class="arr">→</div>
<div class="step"><b>서식별로 나누기</b><span>Classify<br>개인 / 법인 / 공개</span></div><div class="arr">→</div>
<div class="step"><b>칸마다 값 옮겨 적기</b><span>Extract<br>18개 항목</span></div><div class="arr">→</div>
<div class="step"><b>묶음 하나로 모으기</b><span>Merge</span></div><div class="arr">→</div>
<div class="step"><b>못 읽은 곳 표시</b><span>Validate<br>판독 상태</span></div><div class="arr">→</div>
<div class="step hl"><b>등급 매기기</b><span>Instruct 위험도_판정<br>키 4개</span></div><div class="arr">→</div>
<div class="step"><b>다음 조치</b><span>Instruct ×4<br>차단·마스킹·승인·확인요청</span></div></div>
<table class="t"><tr><th>노드</th><th>없으면 생기는 문제</th></tr>
<tr><td>Parse (OCR 강제)</td><td>촬영·스캔본은 글자층이 없어 빈 문서로 읽힘 → 저위험으로 잘못 나감</td></tr>
<tr><td>Classify (분할)</td><td>한 PDF에 서식이 최대 3종 이어져 옴. 나누지 않으면 서식마다 맞는 항목을 못 고르고 값이 섞임</td></tr>
<tr><td>Extract</td><td>원문 전체를 한 번에 판단하면 가려진 '900101-1******'을 노출로 세거나 칸 나뉜 번호를 놓침</td></tr>
<tr><td>Validate</td><td>못 읽은 번호를 '없음'으로 보고 저위험 판정</td></tr></table></section>""")

S.append("""<section><h2>3. 판정 기준 — 숫자와 조건으로 고정</h2>
<table class="t big"><tr><th>등급</th><th>조건 (노출 = 마스킹 문자 *, X, ●, ○가 0개인 전체 값)</th><th>후속 노드</th></tr>
<tr><td class="r1">고위험</td><td>주민등록번호 · 외국인등록번호 · 여권번호 · 운전면허번호 · 카드번호 중 1개 이상 노출</td><td>발송차단_보고</td></tr>
<tr><td class="r2">중위험</td><td>고위험 0개, 계좌번호 · 휴대전화번호 · 주소 · 이메일 · 소득정보 · 신용정보 · 기업재무정보 1개 이상</td><td>마스킹_요청</td></tr>
<tr><td class="r3">저위험</td><td>노출 0개 (모두 가렸거나 공개 정보)</td><td>발송승인_기록</td></tr>
<tr><td class="r4">검토 필요</td><td>판독 불가 문서 1개 이상, 또는 가린 이름 + 회사명 · 직위 · 출생연도가 함께 있음</td><td>담당자_확인요청</td></tr></table>
<p class="note">판정 순서: 검토 필요 → 고위험 → 중위험 → 저위험. 공개 정보(사업자 · 법인등록번호, 사업장 주소, 자본금 · 주식 수, 대표자 생년월일)는 항목에서 제외</p>
<div class="code">risk_level: 고위험<br>detected_items: [주민등록번호, 휴대전화번호]<br>data_subject: 개인<br>reason: 신청자 칸은 가렸지만 배우자 칸의 주민등록번호 870722-2000063 …</div></section>""")

S.append("""<section><h2>4. 신뢰성 설계 — 틀리기 쉬운 상황을 미리 막기</h2>
<table class="t"><tr><th>틀릴 수 있는 상황</th><th>막는 방법</th><th>나오는 값</th></tr>
<tr><td>흐린 촬영본이라 번호를 못 읽음</td><td>readability=unclear면 검증 빨강. 제목·이름·항목이 전부 비면 '읽지 못함'으로 봄</td><td>검토 필요</td></tr>
<tr><td>이름만 가리고 회사·직위·출생연도가 남음</td><td>재식별 위험으로 담당자에게 넘김</td><td>검토 필요</td></tr>
<tr><td>'마스킹 처리본' 표시가 있음</td><td>표시를 믿지 않고 모든 칸을 같은 기준으로 다시 봄</td><td>남은 값 기준</td></tr>
<tr><td>신청자 칸만 가리고 배우자 칸은 그대로</td><td>한 칸이라도 전체 값이면 노출</td><td>고위험</td></tr>
<tr><td>가린 값을 노출로 셈</td><td>출력 전 자기 점검: 가림 없는 값을 근거로 인용할 수 없는 항목은 뺌</td><td>등급 재계산</td></tr>
<tr><td>법인 손익계산서의 '급여'</td><td>개인 소득정보가 아니라 기업재무정보로만 봄</td><td>기업재무정보</td></tr></table>
<p class="note">사람에게 넘기는 장치: 결정값 '검토 필요' → 담당자 확인 메모 + 고객 재제출 요청문 자동 작성</p></section>""")

S.append(f"""<section><h2>5. 데이터셋 — 실제 법정 서식에 가상 값</h2>
<div class="cols"><div><ul>
<li>국가법령정보센터 별지 서식 8종: 근로소득 원천징수영수증, 금융정보 등 제공 동의서, 여권 발급 신청서, 외국인등록사실증명, 표준재무상태표, 표준손익계산서, 주식등변동상황명세서, 사업자등록증</li>
<li><b>14개 묶음 · 문서 21건</b>, 유형 ①~⑤ 모두 포함</li>
<li>정답 분포: 고위험 {dist.get('고위험',0)} · 중위험 {dist.get('중위험',0)} · 저위험 {dist.get('저위험',0)} · 검토 필요 {dist.get('검토 필요',0)}</li>
<li>번호는 가상임이 보이게 0을 채움: 900101-1000017, 010-0000-2847</li></ul></div>
<div class="imgs"><img src="{img('set09', 0, (0.05, 0.08, 0.95, 0.47))}"><span>I — 금융정보 등 제공 동의서 (배우자 칸만 노출)</span></div></div></section>""")

S.append(f"""<section><h2>6. 개선 과정과 결과 — 14건 대조</h2>
<div class="cols"><div class="wide"><table class="t sm"><tr><th>케이스</th><th>서류</th><th>정답</th><th>결과</th><th></th></tr>{''.join(rows)}</table></div>
<div><table class="t"><tr><th>설정</th><th>일치</th><th>고친 점</th></tr>
<tr><td>#4</td><td>11/14</td><td>법정 서식 기준으로 분류·추출 설명 교체</td></tr>
<tr><td>#5</td><td>13/14</td><td>흐린 사진 '판독 실패' 규칙, ○ 가림 문자 추가</td></tr>
<tr><td>#6</td><td>13/14</td><td>서식 2종이 한 범위로 묶여도 모든 쪽을 읽도록 추출 지시 수정</td></tr>
<tr><td>#7</td><td>13/14</td><td>출력 전 자기 점검(가린 값만으로 항목을 넣지 않음)</td></tr>
<tr><td>{e(RES['config'])}</td><td><b>{ok}/14</b></td><td>목록 값을 첫 값만 보지 않고 하나씩 모두 확인</td></tr></table>
<p class="note">위험도 · 노출 항목 · 정보 주인 3개가 모두 같아야 '일치'로 셈</p></div></div></section>""")

g = RES.get("followups", {})
S.append(f"""<section><h2>7. 데모 — 흐린 촬영본은 추측하지 않고 넘김</h2>
<div class="cols"><div class="imgs"><img src="{img('set07', 0, (0, 0, 1, 0.6), 70)}"><span>G — 외국인등록사실증명 휴대폰 촬영본</span></div>
<div><div class="code">{e(RES['raw'].get('set07', '')).replace(chr(10), '<br>')}</div>
<h3>담당자_확인요청 노드 출력</h3><div class="code sm">{e(g.get('set07', '')).replace(chr(10), '<br>')}</div></div></div></section>""")

S.append("""<section><h2>8. 한계와 다음 단계</h2><ul class="big">
<li>같은 설정이어도 실행마다 판단이 조금씩 흔들림 → 출력 전 자기 점검 규칙과 '검토 필요' 경로로 피해를 줄임</li>
<li>재식별 위험(이름 가림 + 조합 정보)은 규칙으로 정한 조합만 잡음 → 실제 민원·보고서 서식으로 사례를 늘릴 예정</li>
<li>최종 발송 판단은 담당자가 함: 이 워크플로우는 1차 점검과 조치 문서 초안까지 맡음</li></ul></section>""")

CSS = """@page{size:1280px 720px;margin:0}*{box-sizing:border-box}body{margin:0;font-family:'Malgun Gothic',sans-serif;color:#1d2433}
section{width:1280px;height:720px;padding:48px 64px;page-break-after:always;position:relative;overflow:hidden;background:#fff;border-top:10px solid #5b4bdb}
h1{font-size:46px;line-height:1.3;margin:24px 0}h2{font-size:30px;margin:0 0 24px;color:#2a2470}h3{font-size:20px;margin:6px 0 8px;color:#5b4bdb}
.title{display:flex;flex-direction:column;justify-content:center;background:#f4f2ff}.kicker{font-size:20px;color:#5b4bdb;font-weight:bold}.sub{font-size:21px;color:#444}
ul{font-size:19px;line-height:1.6;padding-left:22px;margin:0}ul.big{font-size:23px;line-height:1.9}
.cols{display:flex;gap:36px}.cols>div{flex:1}
.note{position:absolute;left:64px;right:64px;bottom:30px;font-size:17px;background:#f4f2ff;padding:10px 16px;border-radius:8px;margin:0}
.flow{display:flex;align-items:stretch;gap:6px;margin-bottom:26px}.step{flex:1;border:2px solid #cfc9f7;border-radius:10px;padding:10px 8px;text-align:center;font-size:15px}
.step b{display:block;font-size:16px;margin-bottom:6px}.step span{color:#555}.step.hl{background:#5b4bdb;color:#fff;border-color:#5b4bdb}.step.hl span{color:#e8e5ff}.arr{align-self:center;color:#5b4bdb;font-size:22px}
table.t{border-collapse:collapse;width:100%;font-size:16px}table.t th{background:#2a2470;color:#fff;padding:7px 10px;text-align:left}table.t td{border-bottom:1px solid #ddd;padding:7px 10px;vertical-align:top}
table.big{font-size:18px}table.sm{font-size:12px}table.sm td,table.sm th{padding:3px 6px;white-space:nowrap}table.sm td.doc{white-space:normal}.wide{flex:1.5!important}
td.r1{color:#c62828;font-weight:bold}td.r2{color:#d97706;font-weight:bold}td.r3{color:#15803d;font-weight:bold}td.r4{color:#5b4bdb;font-weight:bold}
td.y{color:#15803d;font-weight:bold}td.n{color:#c62828;font-weight:bold}
.code{font-family:Consolas,'Malgun Gothic',monospace;background:#1d2433;color:#e6e6e6;padding:14px 18px;border-radius:8px;font-size:15px;line-height:1.5;margin-top:14px}.code.sm{font-size:13px}
.imgs{text-align:center}.imgs img{max-width:100%;max-height:520px;border:1px solid #ccc}.imgs span{display:block;font-size:15px;color:#555;margin-top:6px}"""

page = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(S)}</body></html>"
hp = DECK / "deck.html"
hp.write_text(page, encoding="utf-8")
pdf = OUT / f"{TEAM}_최종제출_발표자료.pdf"
subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", hp.as_uri()], check=True, timeout=120)
print(pdf, fitz.open(pdf).page_count, "pages", f"{ok}/14")
