# -*- coding: utf-8 -*-
"""정답지(answer.json) · 유형표(xlsx) · 워크플로우 설정(workflow.json) · 설계서(docx) 생성."""
import copy, glob, json, sys
from pathlib import Path
import openpyxl
import docx
from docx.shared import RGBColor

TEAM = sys.argv[1] if len(sys.argv) > 1 else "팀명"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "미션2_제출물"
TPL = next((ROOT.parent / "mission2_downloads" / "templates").glob("*"))
f = lambda s: f"{TEAM}_미션2_{s}"

HIGH = ["주민등록번호", "외국인등록번호", "여권번호", "운전면허번호", "카드번호"]
MID = ["계좌번호", "휴대전화번호", "주소", "이메일", "소득정보", "신용정보", "기업재무정보"]
RISK = ["고위험", "중위험", "저위험", "검토 필요"]

# ------------------------------------------------------------------ 정답지
CASES = [
    dict(case_id="A", file=f("set01.pdf"), documents=["개인 여신거래 신청서", "통장 사본(개인)"],
         answer=dict(risk_level="고위험",
                     detected_items=["주민등록번호", "주소", "휴대전화번호", "이메일", "소득정보", "계좌번호"],
                     data_subject="개인",
                     reason="여신거래 신청서에 주민등록번호(920415-1356428)가 가려지지 않아 고위험. 주소·휴대전화번호·이메일·연소득(54,000,000원)과 통장 사본의 계좌번호(508-210-447819)도 노출")),
    dict(case_id="B", file=f("set02.pdf"), documents=["영문 거래내역서(Account Statement, 마스킹)"],
         answer=dict(risk_level="저위험", detected_items=[], data_subject="없음",
                     reason="영문 거래내역서의 예금주(KIM M*** J***)와 계좌번호(508-***-***819)가 마스킹되어 노출된 항목이 없음. 고객센터 번호(1588-0000)와 영업점 주소는 개인정보가 아님")),
    dict(case_id="C", file=f("set03.pdf"), documents=["기업 재무제표 요약(대외비)", "주주명부 사본"],
         answer=dict(risk_level="고위험", detected_items=["기업재무정보", "주민등록번호", "주소"], data_subject="개인·기업",
                     reason="법인 서류인 주주명부에 개인 주주 2명의 주민등록번호(710205-1462318 등)와 거주지 주소가 가려지지 않아 고위험. 대외비 재무제표의 매출액·영업이익·부채비율 등 기업재무정보도 노출(사업자등록번호·본점 소재지는 제외)")),
    dict(case_id="D", file=f("set04.pdf"), documents=["신분증 사본(휴대폰 촬영)"],
         answer=dict(risk_level="검토 필요", detected_items=[], data_subject="없음",
                     reason="휴대폰으로 찍은 신분증 사본이 흐리고 빛이 번져 주민등록번호 노출 여부를 판독할 수 없음")),
    dict(case_id="E", file=f("set05.pdf"), documents=["개인신용정보 조회 결과서", "신용카드 이용대금 명세서('마스킹 완료' 표시)"],
         answer=dict(risk_level="고위험", detected_items=["신용정보", "카드번호"], data_subject="개인",
                     reason="명세서에 '개인정보 마스킹 완료' 표시가 있지만 이용내역 비고란에 카드번호 전체(5310-8821-4093-4471)가 노출되어 고위험. 조회서의 신용평점 712점·대출잔액도 노출(주민등록번호는 마스킹)")),
    dict(case_id="F", file=f("set06.pdf"), documents=["거래내역 확인서(법인, 2쪽)"],
         answer=dict(risk_level="중위험", detected_items=["계좌번호"], data_subject="기업",
                     reason="1쪽 계좌번호는 508-910-***317로 가렸지만 2쪽 머리에 같은 계좌번호 전체(508-910-552317)가 남아 중위험. 법인 계좌라 정보 주인은 기업이며 사업자등록번호·거래처 회사명은 제외")),
    dict(case_id="G", file=f("set07.pdf"), documents=["민원 처리 결과 보고서(비식별 처리본)"],
         answer=dict(risk_level="검토 필요", detected_items=[], data_subject="없음",
                     reason="민원인 이름(이**)과 연락처는 가렸지만 1995년생·(주)동해물류 물류운영팀 대리·앱 업로드 일시가 함께 적혀 누구인지 짐작할 수 있어(재식별 위험) 담당자 확인이 필요")),
    dict(case_id="H", file=f("set08.pdf"), documents=["해외송금 신청서(국·영문 병기, 외국인 고객)"],
         answer=dict(risk_level="고위험", detected_items=["외국인등록번호", "여권번호", "주소", "휴대전화번호", "계좌번호"], data_subject="개인",
                     reason="외국인 고객의 외국인등록번호(930517-5281406)와 여권번호(C4829157)가 가려지지 않아 고위험. 거주지 주소·휴대전화번호와 출금계좌·수취인 계좌번호도 노출(SWIFT 코드·고객센터 번호는 제외)")),
    dict(case_id="I", file=f("set09.pdf"), documents=["전세자금대출 상담 기록지"],
         answer=dict(risk_level="중위험", detected_items=["휴대전화번호", "이메일", "주소"], data_subject="개인",
                     reason="운전면허번호는 28-**-******-**로 가려져 고위험 항목은 없지만, 휴대전화번호(010-5530-8174)·이메일·현 거주지 주소가 그대로 남아 중위험(지점 주소·고객센터 번호는 제외)")),
    dict(case_id="J", file=f("set10.pdf"), documents=["예금 금리 및 수수료 안내문(스캔본)"],
         answer=dict(risk_level="저위험", detected_items=[], data_subject="없음",
                     reason="영업점 게시용 금리·수수료 안내문으로 특정 고객 정보가 없음. 스캔으로 약간 기울고 흐리지만 글자는 읽히며, 고객센터 번호(1588-0000)와 본점 주소는 공개 정보")),
]
answer = {
    "task": "업스은행(가상) 금융 서류 묶음 외부 발송 전 민감정보 자동 식별 및 위험도 등급화 (IM뱅크 지정주제)",
    "unit": "발송 1건 = 파일 1개(서류 묶음 PDF) = 판정 1건",
    "output_keys": ["risk_level", "detected_items", "data_subject", "reason"],
    "decision_values": RISK,
    "detected_items_values": HIGH + MID,
    "data_subject_values": ["개인", "기업", "개인·기업", "없음"],
    "cases": CASES,
}
(OUT / f("answer.json")).write_text(json.dumps(answer, ensure_ascii=False, indent=2), encoding="utf-8")

# ------------------------------------------------------------------ 유형표
ROWS = [
    ("set01.pdf", 1, "A", "개인 여신거래 신청서", "① 단순", "기본 추출: 가려지지 않은 주민등록번호·주소·휴대전화·이메일·연소득 식별", "고위험"),
    ("set01.pdf", 2, "A", "통장 사본(개인)", "① 단순 · ③ 결합", "신청서와 한 PDF로 들어온 통장을 분할해 계좌번호 식별", "고위험"),
    ("set02.pdf", 1, "B", "영문 거래내역서(마스킹)", "② 양식", "영문 양식에서 마스킹된 예금주·계좌번호와 1588 고객센터 번호를 노출로 오인하지 않는지", "저위험"),
    ("set03.pdf", 1, "C", "기업 재무제표 요약(대외비)", "② 양식", "대외비 재무제표의 매출액·영업이익·부채비율을 기업재무정보로 식별 (U139 문서 참고)", "고위험"),
    ("set03.pdf", 2, "C", "주주명부 사본", "③ 결합 · ⑤ 예외", "법인 서류 안의 주주 개인 주민등록번호·주소를 잡아 정보 주인을 '개인·기업'으로 (U139 문서 참고)", "고위험"),
    ("set04.pdf", 1, "D", "신분증 사본(휴대폰 촬영)", "④ 저품질", "흐리고 빛 번진 사진의 주민등록번호를 추측하지 않고 검토 필요로", "검토 필요"),
    ("set05.pdf", 1, "E", "개인신용정보 조회 결과서", "③ 결합 · ⑤ 예외", "마스킹된 주민등록번호는 제외, 신용평점·대출잔액은 신용정보로 식별", "고위험"),
    ("set05.pdf", 2, "E", "신용카드 이용대금 명세서", "⑤ 예외", "'마스킹 완료' 표시에도 비고란에 남은 카드번호 전체를 잡는지", "고위험"),
    ("set06.pdf", "1-2", "F", "거래내역 확인서(법인, 2쪽)", "② 양식 · ⑤ 예외", "같은 계좌번호가 1쪽은 가려지고 2쪽은 그대로인 것을 잡는지, 입출금액을 기업재무정보로 오인하지 않는지 (U108 예외 응용)", "중위험"),
    ("set07.pdf", 1, "G", "민원 처리 결과 보고서(비식별 처리본)", "⑤ 예외", "이름·연락처는 가렸지만 출생연도·직장·직위 조합으로 재식별되는 위험을 검토 필요로 (U108 예외 응용)", "검토 필요"),
    ("set08.pdf", 1, "H", "해외송금 신청서(국·영문 병기)", "② 양식", "국·영문이 섞인 외환 서식에서 외국인등록번호·여권번호를 고위험 항목으로 잡는지, SWIFT 코드는 제외하는지", "고위험"),
    ("set09.pdf", 1, "I", "전세자금대출 상담 기록지", "① 단순 · ⑤ 예외", "가려진 운전면허번호는 빼고, 남은 휴대전화·이메일·주소만으로 중위험이 나오는지", "중위험"),
    ("set10.pdf", 1, "J", "예금 금리·수수료 안내문(스캔본)", "② 양식 · ④ 저품질", "약간 기울고 흐린 스캔이어도 읽히면 판독 불가로 보내지 않고, 공개 자료라 저위험으로", "저위험"),
]
OWNER = {"A": "A 김민준", "B": "B KIM M*** J***", "C": "C (주)대경정밀", "D": "D 이서윤", "E": "E 박지호",
         "F": "F (주)포항해양산업", "G": "G 이**", "H": "H NGUYEN VAN HUNG", "I": "I 정유나", "J": "J 없음(공개 안내문)"}
wb = openpyxl.load_workbook(next(TPL.glob("*유형표*.xlsx")))
ws = wb["유형표"]
ws.delete_rows(2, 3)  # 회색 '예시' 줄 3개 삭제
black = openpyxl.styles.Font(name=ws.cell(2, 2).font.name, size=ws.cell(2, 2).font.sz, color="FF000000")
for i, (fn, pg, cid, kind, typ, purpose, exp) in enumerate(ROWS):
    r = i + 2
    vals = [i + 1, f(fn), pg, OWNER[cid], kind, typ, purpose, exp]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.font = black
for r in range(2 + len(ROWS), ws.max_row + 1):  # 남은 빈 번호 줄 정리
    for c in range(1, 9):
        ws.cell(r, c).value = None
wb.save(OUT / f("유형표.xlsx"))

# ------------------------------------------------------------------ 워크플로우 설정 JSON
def arr(desc):
    return {"type": "array", "items": {"type": "string", "description": desc}, "description": ""}

NOMASK = " 마스킹 문자(*, X, ●)가 섞여 있어도 보이는 그대로 적는다. 문서에 없으면 빈 목록. 추측해서 만들지 않는다."
PROPS = {
    "document_title": {"type": "string", "description": "문서 제목 그대로. 예: '개인 여신거래 신청서', 'ACCOUNT STATEMENT'. 없으면 빈 문자열."},
    "owner_type": {"type": "string", "description": "이 문서 정보의 주인. 개인 고객 서류면 '개인', 법인(회사) 서류면 '기업', 상품설명서·약관 같은 공개 자료면 '공개'."},
    "resident_reg_numbers": arr("주민등록번호(6자리-7자리) 형태의 값 전부." + NOMASK),
    "foreigner_reg_numbers": arr("외국인등록번호 값 전부." + NOMASK),
    "passport_numbers": arr("여권번호 값 전부." + NOMASK),
    "driver_license_numbers": arr("운전면허번호(예: 11-12-345678-90) 값 전부." + NOMASK),
    "card_numbers": arr("신용·체크카드 번호(4-4-4-4, 16자리) 전부. 표 머리뿐 아니라 이용내역·비고란·메모에 적힌 번호까지 모두." + NOMASK),
    "account_numbers": arr("은행 계좌번호 전부(개인·법인). 사업자등록번호(3-2-5자리), 고객센터 번호, 조회·접수·관리번호는 넣지 않는다." + NOMASK),
    "mobile_numbers": arr("휴대전화번호(010·011 등으로 시작). 1588 같은 대표번호·고객센터 번호는 넣지 않는다." + NOMASK),
    "personal_addresses": arr("개인 고객의 거주지·청구지 주소. 은행 영업점·본점 주소, 회사·법인 소재지 주소는 넣지 않는다." + NOMASK),
    "emails": arr("이메일 주소 전부. 은행 홈페이지 주소(www)는 넣지 않는다." + NOMASK),
    "income_values": arr("개인의 연소득·월급여·원천징수 소득처럼 '소득'으로 적힌 금액 문구. 예: '연소득 54,000,000원'. 거래내역의 입금액, 상품 우대조건 설명 문구는 넣지 않는다."),
    "credit_values": arr("개인신용정보 문구: 신용평점·신용등급·연체 이력·대출 잔액·카드 이용액. 예: '신용평점 712점'."),
    "corporate_financials": arr("법인 재무제표·결산 자료의 비공개 계정 수치 문구: 매출액·영업이익·당기순이익·자산·부채·부채비율 등. 예: '2025 매출액 41,965'. 거래내역서의 입출금·잔액, 주식 수·지분율은 넣지 않는다."),
    "person_names": arr("문서에 적힌 개인 이름 전부(고객·주주·민원인 등). 마스킹 문자가 있으면 그대로. 예: '김민준', '박*호', '이**'. 은행 직원·회사 대표 직함 옆 이름도 포함. 없으면 빈 목록."),
    "quasi_identifiers": arr("이름이 없어도 특정인을 짐작하게 하는 개인 정보 문구: 출생연도·나이, 성별, 다니는 회사명, 부서·직위, 구체적인 접수·업로드 일시. 문구 그대로. 법인 자체 정보나 상품 설명은 넣지 않는다."),
    "masking_stamp": {"type": "boolean", "description": "문서에 '마스킹 완료', 'masked' 같은 표시가 있으면 true, 없으면 false."},
    "readability": {"type": "string", "description": "판독 상태. 모든 글자·숫자가 또렷하면 'clear', 사진 흐림·빛 번짐·기울어짐으로 번호나 글자를 읽을 수 없는 부분이 있으면 'unclear'."},
}
SYS = "[문서 경계] 입력 파일은 발송 1건의 서류 여러 종류가 한 PDF로 이어 붙은 묶음이며 앞 단계에서 문서 단위로 분리된다. 다른 문서에 속한 값을 이 문서의 값으로 가져오지 않는다. 값은 고치거나 가리지 말고 문서에 보이는 그대로 옮긴다."

def schema(name):
    return {"type": "json_schema", "json_schema": {"name": name, "schema": {"type": "object", "properties": copy.deepcopy(PROPS)}},
            "mode": "standard", "modelName": "", "userSystemPrompt": SYS}

JUDGE = f"""당신은 업스은행 개인정보보호 담당자의 1차 점검 보조자다. 앞 단계에서 문서별로 추출된 결과만 사용해, 이 서류 묶음을 외부로 보내기 전 민감정보 노출 위험도를 판정하라.
문서에 없는 값은 절대 만들지 마라. 확신이 없으면 단정하지 말고 '검토 필요'로 표기하라. 본 결과는 1차 스크리닝이며 최종 발송 판단은 담당자가 한다.

[노출 판단] 추출된 값에 마스킹 문자(*, X, ●)가 하나라도 있으면 가려진 값이므로 노출로 세지 않는다. 마스킹 문자 없이 전체 값이 보일 때만 노출이다.
'마스킹 완료' 표시(masking_stamp)가 있어도 믿지 말고 모든 값을 같은 기준으로 다시 본다.
사업자등록번호, 고객센터·대표번호, 은행 영업점·회사 소재지 주소, 조회·접수번호는 공개 정보이므로 어떤 항목에도 넣지 않는다.

[detected_items 항목 이름 — 아래 12개 이름만 그대로 쓴다]
고위험 항목: {", ".join(HIGH)}
중위험 항목: {", ".join(MID)}
대응: resident_reg_numbers→주민등록번호, foreigner_reg_numbers→외국인등록번호, passport_numbers→여권번호, driver_license_numbers→운전면허번호, card_numbers→카드번호, account_numbers→계좌번호, mobile_numbers→휴대전화번호, personal_addresses→주소, emails→이메일, income_values→소득정보, credit_values→신용정보, corporate_financials→기업재무정보.
노출된 값이 하나 이상 있는 항목만, 항목 이름을 한 번씩만 적는다.

[판정 순서 — 반드시 이 순서로]
- 1단계 '검토 필요': 아래 중 하나라도 해당하면 '검토 필요'로 판정하고 더 진행하지 않는다. 이때 detected_items는 또렷한 문서에서 확인된 노출 항목만 적는다.
  (a) 판독 불가: readability가 'unclear'인 문서가 있어 번호 노출 여부를 확인할 수 없음.
  (b) 재식별 위험: person_names의 개인 이름이 마스킹되어 있는데, 같은 문서의 quasi_identifiers에 다니는 회사명과 부서·직위와 출생연도(또는 나이)가 함께 적혀 있어 누구인지 짐작할 수 있음. 이름이 가려지지 않은 문서에는 적용하지 않는다.
- 2단계 '고위험': 고위험 항목이 하나라도 노출.
- 3단계 '중위험': 고위험 항목은 없고 중위험 항목이 하나 이상 노출.
- 4단계 '저위험': 노출 항목이 하나도 없음(모두 마스킹되었거나 공개 자료).

[data_subject] 노출된 정보의 주인을 적는다. detected_items가 비어 있으면 '없음'.
주민등록번호·외국인등록번호·여권번호·운전면허번호·휴대전화번호·주소·이메일·소득정보·신용정보는 문서 종류와 상관없이 개인의 정보다(법인 서류인 주주명부 속 주주 주민등록번호도 개인).
기업재무정보는 기업의 정보다. 계좌번호·카드번호는 예금주·회원이 개인이면 개인, '(주)' 같은 법인이면 기업이다.
개인 정보만 있으면 '개인', 기업 정보만 있으면 '기업', 둘 다 있으면 '개인·기업'.

[출력] 아래 키 네 개를 이 순서로, 한 줄에 하나씩 작성하라.
risk_level: <고위험 | 중위험 | 저위험 | 검토 필요 중 하나>
detected_items: <노출 항목 이름 목록. 예: [주민등록번호, 계좌번호]. 없으면 []>
data_subject: <개인 | 기업 | 개인·기업 | 없음>
reason: <판정 근거 1~2문장. 어떤 문서의 어떤 항목이 실제 값과 함께 노출됐는지, 또는 무엇이 가려졌거나 판독 불가·재식별 위험인지>
마지막 줄에 risk_level 값만 한 번 더 적어라."""

FOLLOW = {
    "발송차단_보고": ("고위험", "앞선 판정 [[위험도_판정]] 결과가 '고위험'인 건이다. 문서에 없는 값은 절대 만들지 마라.\n담당자용 발송 차단 보고를 작성하라: 제목(외부 발송 차단 — 고위험 민감정보 노출) / 노출 항목과 위치(문서명·칸 이름) 표 / 즉시 조치(발송 중지, 해당 칸 마스킹 후 재점검) / 보고 대상(개인정보보호 담당). 번호는 앞 4자리만 쓰고 나머지는 *로 가려 적는다. 300자 이내."),
    "마스킹_요청": ("중위험", "앞선 판정 [[위험도_판정]] 결과가 '중위험'인 건이다. 문서에 없는 값은 절대 만들지 마라.\n담당자용 마스킹 요청서를 작성하라: 가려야 할 항목 목록(문서명·항목) / 권장 마스킹 방식(계좌번호 가운데 자리, 주소 동·호수, 이메일 아이디 등) / 마스킹 후 발송 가능 안내. 번호는 일부를 *로 가려 적는다. 300자 이내."),
    "발송승인_기록": ("저위험", "앞선 판정 [[위험도_판정]] 결과가 '저위험'인 건이다. 문서에 없는 값은 절대 만들지 마라.\n발송 승인 기록을 한 단락으로 작성하라: 점검 결과(노출 항목 없음), 확인한 문서 목록, 마스킹·공개 자료 여부, '최종 발송은 담당자 확인 후' 문구. 200자 이내."),
    "담당자_확인요청": ("검토 필요", "앞선 판정 [[위험도_판정]] 결과가 '검토 필요'인 건이다. 문서에 없는 값은 절대 만들지 마라.\n(1) 담당자 확인 메모: 검토 필요 사유(판독 불가 / 재식별 위험)와 해당 문서 이름, 담당자가 원본에서 확인할 것. (2) 후속 요청문: 판독 불가면 고객에게 선명한 사본 재제출 요청(기한은 '담당자 지정'으로 비워 둠), 재식별 위험이면 작성 부서에 회사명·직위·출생연도 같은 조합 정보를 지우거나 범주로 바꿔 달라는 요청. 300자 이내, 존댓말."),
}
UNCLASS = "이 문서는 개인 서류·법인 서류·공개 자료 어디에도 분류되지 않았다. 문서에 없는 값은 절대 만들지 마라.\n한 줄로 작성하라: likely_document_type=<문서가 무엇으로 보이는지>, review_reason=<왜 분류되지 않았는지>, operator_action=<담당자가 할 일: 무시 / 수동 점검 / 고객에게 확인>."

CLASSES = [
    ("personal_doc", "개인 고객 서류. 여신거래 신청서, 개인 통장 사본, 개인 거래내역서(국문·영문 Account Statement), 신분증 사본(주민등록증·운전면허증·여권), 재직증명서·소득증빙, 개인신용정보 조회 결과서, 신용카드 이용대금 명세서, 고객 민원 처리 보고서처럼 한 사람의 고객 정보가 담긴 문서. 휴대폰으로 찍은 흐린 사진이어도 신분증 모양이면 이 범주다."),
    ("corporate_doc", "법인(회사) 서류. 기업 재무제표·재무상태표·손익계산서, 법인 통장 사본, 법인 거래내역 확인서, 주주명부, 사업자등록증, 법인 여신 심사 자료처럼 예금주·주인이 '(주)' 같은 법인인 문서."),
    ("public_doc", "공개 자료. 상품설명서, 금리·수수료 안내문, 약관, 광고 전단처럼 특정 고객 정보 없이 누구에게나 주는 문서."),
    ("Other", "위 세 범주에 해당하지 않거나 판독이 어려운 문서. 예: 빈 페이지, 은행과 무관한 문서."),
]
EXT = {"personal_doc": "개인서류_추출", "corporate_doc": "법인서류_추출", "public_doc": "공개자료_추출"}

edges, n = [], 0
def edge(src, tgt, cond=None):
    global n
    e = {"id": f"e{n}", "source": src, "target": tgt}
    if cond:
        e["condition"] = {"conditionName": cond}
    edges.append(e); n += 1
CL = {"nodeType": "classify", "name": "금융서류-분류"}
edge({"nodeType": "parse"}, CL)
for cls, sch in EXT.items():
    edge(CL, {"nodeType": "extract", "name": sch}, cls)
edge(CL, {"nodeType": "instruct", "name": "미분류_안내"}, "Other")
for sch in EXT.values():
    edge({"nodeType": "extract", "name": sch}, {"nodeType": "merge", "name": "병합-1"})
edge({"nodeType": "merge", "name": "병합-1"}, {"nodeType": "instruct", "name": "위험도_판정"})
for name, (cond, _) in FOLLOW.items():
    edge({"nodeType": "instruct", "name": "위험도_판정"}, {"nodeType": "instruct", "name": name}, cond)

NAME = f"{TEAM}_미션2_금융문서 민감정보 위험도 등급화"
wf = {
    "kind": "studio.agent-config-draft",
    "exportedAt": "2026-11-05T00:00:00.000Z",
    "exportedFrom": {"agentId": "", "agentName": NAME, "configId": "", "configVer": 1},
    "agentConfig": {
        "agent_name": NAME,
        "pipelineType": "instruct",
        "documentParseConfiguration": {"modelName": "document-parse", "mode": "standard", "ocrMode": "force", "lang": "",
                                       "chartRecognition": False, "coordinates": True, "mergeMultipageTables": False,
                                       "outputFormats": ["html", "text"], "base64Encoding": ["figure"], "customName": "금융서류-파싱"},
        "documentClassifyConfiguration": {"modelName": "", "schema": {"type": "json_schema", "json_schema": {"name": "document-classify", "schema": {
            "type": "string", "oneOf": [{"const": c, "description": d} for c, d in CLASSES]}}},
            "customName": "금융서류-분류", "split": True, "splitCriteria": [{"criterion": "CONTINUITY", "description": ""}]},
        "informationExtractConfiguration": {"modelName": "", "schemas": [schema(s) for s in EXT.values()],
                                            "categorySchemaMapping": dict(EXT), "location": True},
        "instructConfiguration": {
            "nodes": [{"name": "위험도_판정", "modelName": "", "prompt": JUDGE, "enumEnabled": True, "enumValues": RISK}]
                     + [{"name": k, "modelName": "", "prompt": v[1]} for k, v in FOLLOW.items()]
                     + [{"name": "미분류_안내", "modelName": "", "prompt": UNCLASS}],
            "connectionMapping": {**{k: {"targetType": "instruct", "instructNodeName": "위험도_판정"} for k in FOLLOW},
                                  "미분류_안내": {"targetType": "classify", "classifyClassName": "Other"}}},
        "pipelineEdges": edges,
    },
}
# Studio에서 내보낸 workflow.json을 덮어쓰지 않음
if False: (OUT / f("workflow.json")).write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")

# ------------------------------------------------------------------ 설계서
d = docx.Document(next(TPL.glob("*설계서*.docx")))
BLACK = RGBColor(0x11, 0x11, 0x11)

def set_cell(cell, text):
    p = cell.paragraphs[0]
    runs = p.runs
    if runs:
        runs[0].text = text
        runs[0].font.color.rgb = BLACK
        for r in runs[1:]:
            r.text = ""
    else:
        p.add_run(text).font.color.rgb = BLACK
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)

def fill(table, rows, start=1):
    while len(table.rows) - start < len(rows):
        table._tbl.append(copy.deepcopy(table.rows[-1]._tr))
    for i, vals in enumerate(rows):
        for j, v in enumerate(vals):
            set_cell(table.rows[start + i].cells[j], v)

t0, t1, t2, t3 = d.tables
for i, v in enumerate([TEAM, "IM뱅크 지정주제 — AI 기반 금융 문서 민감 정보 자동 식별 및 위험도 등급화",
                       NAME, "없음 (IM뱅크 지정주제 트랙)", "해당 없음"]):
    set_cell(t0.rows[i].cells[1], v)

P = d.paragraphs
def set_para(p, label, text):
    for r in p.runs[1:]:
        r.text = ""
    p.runs[0].text = label
    p.add_run(text).font.color.rgb = BLACK

set_para(P[5], "업무: ", "은행 담당자가 서류 묶음을 외부로 보내기 전에 가려지지 않은 민감정보를 찾아 위험도 4단계로 1차 등급화")
set_para(P[6], "문서: ", "13건(PDF 10개, 발송 1건 = PDF 1개) — 여신 신청서, 통장, 거래내역서, 재무제표, 주주명부, 신분증, 신용조회서, 카드명세서, 민원보고서, 해외송금 신청서, 상담 기록지, 금리 안내문")
set_para(P[7], "선정 이유: ", "개인·법인 서류가 섞여 오고, '마스킹 완료' 표시만 믿고 보냈다가 비고란의 번호가 새는 사고가 생김")
set_para(P[8], "판정 기준: ", "고위험=주민·외국인등록·여권·면허·카드번호 노출 / 중위험=계좌·연락처·주소·이메일·소득·신용·재무만 / 저위험=노출 없음 / 판독 불가·재식별=검토 필요")
for i in (2, 4, 10, 12, 14):  # 회색 안내 문구 삭제
    P[i]._element.getparent().remove(P[i]._element)

fill(t1, [
    ("risk_level", "고위험 | 중위험 | 저위험 | 검토 필요", "네 값 중 하나만"),
    ("detected_items", "문자열 배열", "노출 항목 이름(정해진 12개 중), 없으면 []"),
    ("data_subject", "개인 | 기업 | 개인·기업 | 없음", "노출 정보의 주인"),
    ("reason", "문자열 (1~2문장)", "어떤 문서의 어떤 값이 노출·마스킹·판독 불가인지"),
])
fill(t2, [
    ("1", "Parse", "휴대폰 사진·스캔본까지 읽도록 OCR 강제"),
    ("2", "Classify (분할)", "한 PDF에 섞인 서류를 개인 / 법인 / 공개 문서로 나눔"),
    ("3", "Extract", "세 종류 모두 같은 항목으로, 번호·연락처·주소·소득·신용·재무 값을 마스킹 문자까지 그대로 뽑음"),
    ("4", "Merge", "묶음 전체 추출 결과를 합쳐 발송 1건으로 판정"),
    ("5", "Validate", "판독 상태 clear(필수·빨강), 신뢰도 기준(선택·노랑)으로 위험 신호 먼저 표시"),
    ("6", "Instruct 위험도_판정", "검토 필요→고위험→중위험→저위험 순으로 키 4개 작성, 값으로 분기"),
    ("7", "Instruct ×4", "판정 값별로 발송 차단 / 마스킹 요청 / 발송 승인 / 담당자 확인 문구 작성"),
], start=1)
fill(t3, [
    ("신분증 사진이 흐려 판독 불가", "번호를 추측하지 않고 넘김", "검토 필요"),
    ("'마스킹 완료'인데 비고란에 번호", "표시를 믿지 않고 모든 칸을 검사", "고위험"),
    ("이름만 가리고 나이·직장·직위 남음", "재식별 위험으로 보고 넘김", "검토 필요"),
    ("계좌번호를 1쪽만 가리고 2쪽은 그대로", "한 곳이라도 전체가 보이면 노출", "중위험(계좌)"),
    ("사업자번호·고객센터 번호·회사 주소", "공개 정보라 제외", "항목에서 제외"),
])

# ---- 1장 분량으로 압축: 글자·줄간격·셀 여백 축소
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
def tighten(par, size):
    pf = par.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(1); pf.line_spacing = 1.0
    for r in par.runs:
        r.font.size = Pt(size)
for par in d.paragraphs:
    st = par.style.name
    size = 13 if st == "Title" else 10 if st.startswith("Heading") else 8
    tighten(par, size)
    if st.startswith("Heading"):
        par.paragraph_format.space_before = Pt(3)
for t in d.tables:
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        for h in trPr.findall(qn("w:trHeight")):
            trPr.remove(h)
        for cell in row.cells:
            for par in cell.paragraphs:
                tighten(par, 8)
            tcPr = cell._tc.get_or_add_tcPr()
            for m in tcPr.findall(qn("w:tcMar")):
                tcPr.remove(m)
            mar = OxmlElement("w:tcMar")
            for side in ("top", "bottom"):
                e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "15"); e.set(qn("w:type"), "dxa"); mar.append(e)
            tcPr.append(mar)
for sec in d.sections:
    from docx.shared import Cm
    sec.top_margin = sec.bottom_margin = Cm(1.0)
d.save(OUT / f("설계서.docx"))
print("ok")
