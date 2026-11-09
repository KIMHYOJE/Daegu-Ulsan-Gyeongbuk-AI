# -*- coding: utf-8 -*-
"""최종 제출 설계서(docx → pdf). 실제 Studio 에이전트 "요미의 코딩" 설정 #1과 같은 내용으로 작성."""
import copy, glob, sys
from pathlib import Path
import docx
from docx.shared import RGBColor, Pt, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TEAM = sys.argv[1] if len(sys.argv) > 1 else "팀명"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "최종제출_제출물"
TPL = next((ROOT.parent / "mission2_downloads" / "templates").glob("*"))
NAME = TEAM  # Studio 에이전트 이름 (라이브러리 게시·workflow.json과 같음)
BLACK = RGBColor(0x11, 0x11, 0x11)

d = docx.Document(next(TPL.glob("*설계서*.docx")))


def set_cell(cell, text, bold=False):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
        run = p.runs[0]
    else:
        run = p.add_run(text)
    run.font.color.rgb = BLACK
    run.bold = bold or None
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def fill(table, rows, start=1):
    while len(table.rows) - start < len(rows):
        table._tbl.append(copy.deepcopy(table.rows[-1]._tr))
    while len(table.rows) - start > len(rows):
        table._tbl.remove(table.rows[-1]._tr)
    for i, vals in enumerate(rows):
        for j, v in enumerate(vals):
            set_cell(table.rows[start + i].cells[j], v)


def set_para(p, label, text):
    for r in p.runs[1:]:
        r.text = ""
    p.runs[0].text = label
    p.runs[0].font.color.rgb = BLACK
    p.add_run(text).font.color.rgb = BLACK


t0, t1, t2, t3 = d.tables
P = d.paragraphs
P[0].runs[0].text = "최종 설계서"
for r in P[0].runs[1:]:
    r.text = ""
P[1].runs[0].text = "- 금융문서 민감정보 위험도 등급화 워크플로우 (Studio 설정 #1) -"
for r in P[1].runs[1:]:
    r.text = ""

for i, v in enumerate([TEAM, "IM뱅크 지정주제 — AI 기반 금융 문서 민감 정보 자동 식별 및 위험도 등급화",
                       f"{NAME} (설정 #1)", "없음 (IM뱅크 지정주제)",
                       "카드 미사용. 미션 2 이후 분류·추출 설명을 법정 서식 기준으로 고침"]):
    set_cell(t0.rows[i].cells[1], v)

set_para(P[5], "업무: ", "은행 개인정보보호 담당자가 서류 묶음을 외부로 보내기 전, 가려지지 않은 민감정보를 찾아 4단계로 1차 판정")
set_para(P[6], "문서: ", "21건, 14개 묶음(발송 1건 = PDF 1개) — 국가법령정보센터 별지 서식 8종: 원천징수영수증, 금융정보 제공 동의서, 여권 발급 신청서, "
                       "외국인등록사실증명, 표준재무상태표, 표준손익계산서, 주식등변동상황명세서, 사업자등록증")
set_para(P[7], "선정 이유: ", "개인·법인 서식이 섞여 오고, 일부 칸만 가린 서류를 그대로 보내 번호가 새는 일이 생김")
set_para(P[8], "판정 기준: ", "노출 = 마스킹 문자(*, X, ●, ○)가 0개인 전체 값. 고위험 = 주민·외국인등록·여권·운전면허·카드번호 중 1개 이상 노출 / "
                           "중위험 = 고위험 0개이고 계좌·휴대전화·주소·이메일·소득·신용·기업재무정보 1개 이상 / 저위험 = 노출 0개 / "
                           "검토 필요 = 판독 불가 문서 1개 이상, 또는 가린 이름 + 회사명·직위·출생연도")
for i in (14, 12, 10, 4, 2):  # 회색 안내 문구 삭제 (뒤에서부터)
    P[i]._element.getparent().remove(P[i]._element)

fill(t1, [
    ("risk_level", "고위험 | 중위험 | 저위험 | 검토 필요", "네 값 중 하나. 위험도_판정 노드가 키 4개를 함께 출력"),
    ("detected_items", "문자열 배열", "노출 항목 이름(정해진 12개 중), 없으면 []"),
    ("data_subject", "개인 | 기업 | 개인·기업 | 없음", "노출 정보의 주인. 노출 0개면 없음"),
    ("reason", "문자열 (1~2문장)", "어떤 문서의 어떤 값이 노출·마스킹·판독 불가인지"),
])
fill(t2, [
    ("1", "Parse (OCR 강제)", "촬영·스캔본은 글자층이 없는 이미지 PDF라, OCR을 끄면 빈 문서로 읽혀 '노출 없음 → 저위험'으로 잘못 나감"),
    ("2", "Classify 분류-1", "한 PDF에 최대 3종 서식이 이어져 와서, 나누지 않으면 다른 서식의 값이 섞임. 3분기 모두 같은 추출로 보냄(법인 주주 명세에도 개인 번호가 있음)"),
    ("3", "Extract 금융서류_추출", "18항목을 칸별로 뽑고 마스킹 문자는 그대로 둠. 없으면 '900101-1******'을 노출로 세거나 칸마다 나뉜 번호를 놓침"),
    ("4", "Merge 병합-1", "판정 단위가 발송 1건(PDF 1개)이라 문서별 결과를 합침. 없으면 같은 묶음에 문서마다 다른 등급이 나옴"),
    ("5", "Validate 검증-1", "readability = clear 필수(빨강), 주민등록번호 신뢰도 ≥ 0.8(노랑). 없으면 못 읽은 번호를 '없음'으로 보고 저위험으로 판정"),
    ("6", "Instruct 위험도_판정", "검토 필요 → 고위험 → 중위험 → 저위험 순서로 키 4개를 한 노드에서 출력하고 결정값으로 분기. 묶음 전체에서 가장 높은 등급 하나를 정해야 해서 순서를 고정"),
    ("7", "Instruct ×4", "고위험 발송차단_보고 / 중위험 마스킹_요청 / 저위험 발송승인_기록 / 검토 필요 담당자_확인요청(재제출·정보 삭제 요청문). 판정별로 담당자의 다음 행동을 바로 적어 줌"),
], start=1)
fill(t3, [
    ("촬영·스캔본이 흐려 번호를 못 읽음", "readability=unclear(검증 빨강) 또는 제목·이름·항목 모두 빔", "검토 필요"),
    ("가린 이름 + 회사명·직위·출생연도", "재식별 위험으로 보고 담당자에게 넘김", "검토 필요"),
    ("'개인정보 마스킹 처리본' 표시", "표시를 믿지 않고 모든 칸을 같은 기준으로 다시 봄", "남은 값 기준"),
    ("신청자 칸은 가리고 배우자 칸은 그대로", "한 칸이라도 전체 값이 보이면 노출", "고위험"),
    ("사업자·법인등록번호, 사업장 주소, 자본금 / 법인 급여 계정", "공개 정보는 제외 / 회사 급여는 소득정보가 아닌 기업재무정보로만 봄", "항목 제외 / 기업재무정보"),
])

# ---- 1장 분량
def tighten(par, size):
    pf = par.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(1); pf.line_spacing = 1.0
    for r in par.runs:
        r.font.size = Pt(size)

for par in d.paragraphs:
    st = par.style.name
    tighten(par, 13 if st == "Title" else 9.5 if st.startswith("Heading") else 7.5)
    if st.startswith("Heading"):
        par.paragraph_format.space_before = Pt(2)
for t in d.tables:
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        for h in trPr.findall(qn("w:trHeight")):
            trPr.remove(h)
        for cell in row.cells:
            for par in cell.paragraphs:
                tighten(par, 7.5)
            tcPr = cell._tc.get_or_add_tcPr()
            for m in tcPr.findall(qn("w:tcMar")):
                tcPr.remove(m)
            mar = OxmlElement("w:tcMar")
            for side in ("top", "bottom"):
                e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "10"); e.set(qn("w:type"), "dxa"); mar.append(e)
            tcPr.append(mar)
for sec in d.sections:
    sec.top_margin = Cm(0.7); sec.bottom_margin = Cm(0.6)
from docx.shared import Cm as _Cm
def widths(t, ws):
    tblPr = t._tbl.tblPr
    for e in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(e)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), ws):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in t.rows:
        for c, w in zip(row.cells, ws):
            c.width = _Cm(w)
widths(t2, [1.0, 3.4, 13.6])
widths(t3, [5.8, 8.4, 3.8])
widths(t1, [2.8, 5.6, 9.6])
body = d.element.body
last = body[-2] if body[-1].tag == qn("w:sectPr") else body[-1]
if last.tag == qn("w:p"):  # 마지막 표 뒤 빈 문단을 1pt로 줄여 2쪽으로 밀리지 않게
    from docx.text.paragraph import Paragraph
    lp = Paragraph(last, d._body)
    lp.paragraph_format.space_before = Pt(0); lp.paragraph_format.space_after = Pt(0)
    lp.paragraph_format.line_spacing = Pt(1)
    rpr = OxmlElement("w:rPr"); sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); rpr.append(sz)
    ppr = last.get_or_add_pPr(); ppr.append(rpr)
dst = OUT / f"{TEAM}_최종제출_설계서.docx"
d.save(dst)
print(dst)
