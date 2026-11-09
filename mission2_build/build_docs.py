# -*- coding: utf-8 -*-
"""미션 2 테스트 데이터셋 v0 생성기 (가상 금융 문서 10건 / 세트 5개).

HTML로 문서를 만들고 headless Edge로 PDF를 찍는다.
저품질 문서는 Edge 스크린샷을 PIL로 흐리게·기울게 만든 뒤 이미지 페이지로 넣는다.
사용법: python build_docs.py <팀명>
"""
import base64, io, os, subprocess, sys, random
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance

TEAM = sys.argv[1] if len(sys.argv) > 1 else "팀명"
ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
OUT = ROOT.parent / "미션2_제출물"
WORK.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FOOT = "※ 해커톤 실습용 가상 문서 — 업스은행·고객·법인·번호는 모두 가상이며 실제 기관·개인과 관계없습니다."

CSS = """
@page { size: A4; margin: 14mm 14mm 12mm 14mm; }
* { box-sizing: border-box; }
body { font-family: 'Malgun Gothic', sans-serif; color:#111; font-size: 11.5px; margin:0; }
.page { page-break-after: always; position: relative; min-height: 268mm; }
.page:last-child { page-break-after: auto; }
h1 { text-align:center; font-size: 22px; letter-spacing: 6px; margin: 10px 0 4px; }
h2 { font-size: 13px; margin: 14px 0 4px; border-left: 4px solid #1d4e89; padding-left:6px; }
.sub { text-align:center; color:#444; font-size: 11px; margin-bottom: 10px; }
.top { display:flex; justify-content:space-between; font-size:10.5px; color:#333; }
.bank { font-weight:700; color:#1d4e89; font-size: 15px; }
table { width:100%; border-collapse: collapse; margin: 4px 0; }
th, td { border: 1px solid #444; padding: 5px 6px; vertical-align: middle; }
th { background:#eef2f7; width: 17%; font-weight:600; text-align:center; }
td.r { text-align:right; }
.foot { position:absolute; bottom:0; left:0; right:0; text-align:center; font-size:9px; color:#888; }
.stamp { display:inline-block; border: 2px solid #c0392b; color:#c0392b; padding: 4px 10px; font-weight:700; }
.seal { display:inline-block; border:2px solid #c0392b; color:#c0392b; width:54px; height:54px; border-radius:6px; text-align:center; line-height:16px; font-size:11px; padding-top:4px; font-weight:700; }
.small { font-size: 10px; color:#444; }
.box { border:1px solid #444; padding: 8px; }
.en { font-family: Arial, sans-serif; }
"""


def page(body):
    return f'<div class="page">{body}<div class="foot">{FOOT}</div></div>'


def html_doc(pages):
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'


def edge_pdf(html_path, pdf_path):
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


def edge_png(html_path, png_path, w, h):
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", f"--screenshot={png_path}", html_path.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


# ---------------------------------------------------------------- set01 (A)
def set01():
    p1 = page("""
<div class="top"><span class="bank">업스은행</span><span>[여신-01 서식] 접수번호: 2026-대구북-04417</span></div>
<h1>개인 여신거래 신청서</h1><div class="sub">업스은행 여신거래기본약관에 따라 아래와 같이 대출을 신청합니다.</div>
<h2>1. 신청인 정보</h2>
<table>
<tr><th>성 명</th><td>김민준</td><th>주민등록번호</th><td>920415-1356428</td></tr>
<tr><th>주 소</th><td colspan="3">대구광역시 북구 대학로 80, 101동 1203호 (산격동)</td></tr>
<tr><th>휴대전화</th><td>010-2847-6610</td><th>이메일</th><td>minjun.kim92@example.com</td></tr>
</table>
<h2>2. 직장 및 소득</h2>
<table>
<tr><th>직장명</th><td>(주)한빛소프트</td><th>직 위</th><td>선임연구원</td></tr>
<tr><th>입사일</th><td>2019-03-04</td><th>연소득</th><td>54,000,000원 (2025년 원천징수 기준)</td></tr>
</table>
<h2>3. 대출 신청 내용</h2>
<table>
<tr><th>상품명</th><td>업스 직장인 신용대출</td><th>신청금액</th><td>30,000,000원</td></tr>
<tr><th>대출기간</th><td>12개월 (만기일시상환)</td><th>자금용도</th><td>생활자금</td></tr>
<tr><th>입금계좌</th><td colspan="3">본인 명의 업스은행 계좌 (통장 사본 첨부)</td></tr>
</table>
<h2>4. 개인(신용)정보 수집·이용 동의</h2>
<div class="box small">여신거래 심사를 위해 고유식별정보, 연락처, 소득정보, 신용정보를 수집·이용합니다. 보유기간은 거래 종료 후 5년입니다. ☑ 동의함 ☐ 동의하지 않음</div>
<p style="text-align:center;margin-top:28px">2026년 11월 02일</p>
<p style="text-align:right;margin-right:40px">신청인 : 김민준 (서명) &nbsp; <span class="seal">김민<br>준인</span></p>
<p class="small">업스은행 대구북지점장 귀하 &nbsp;|&nbsp; 접수자: 여신담당 정하은</p>
""")
    p2 = page("""
<div class="top"><span class="bank">업스은행</span><span>통장 사본 (계좌개설 확인용)</span></div>
<h1>보 통 예 금 통 장</h1>
<div class="box" style="margin-top:20px">
<table>
<tr><th>예금종류</th><td>업스 자유입출금 보통예금</td></tr>
<tr><th>계좌번호</th><td style="font-size:15px;font-weight:700;letter-spacing:1px">508-210-447819</td></tr>
<tr><th>예 금 주</th><td>김민준</td></tr>
<tr><th>개 설 일</th><td>2019-03-11</td></tr>
<tr><th>개설지점</th><td>업스은행 대구북지점 (지점코드 0508)</td></tr>
</table>
</div>
<h2>최근 거래 (통장 1면)</h2>
<table>
<tr><th style="width:20%">거래일</th><th>적요</th><th style="width:18%">출금</th><th style="width:18%">입금</th><th style="width:20%">잔액</th></tr>
<tr><td>2026-10-24</td><td>급여 (주)한빛소프트</td><td class="r"></td><td class="r">3,912,400</td><td class="r">5,228,910</td></tr>
<tr><td>2026-10-26</td><td>관리비 자동이체</td><td class="r">214,300</td><td class="r"></td><td class="r">5,014,610</td></tr>
<tr><td>2026-10-29</td><td>카드대금</td><td class="r">1,208,550</td><td class="r"></td><td class="r">3,806,060</td></tr>
</table>
<p class="small" style="margin-top:20px">본 사본은 대출금 입금계좌 확인 목적으로만 사용합니다.</p>
""")
    return [p1, p2]


# ---------------------------------------------------------------- set02 (B)
def set02():
    rows = [("2026-10-02", "DEPOSIT (ONLINE)", "", "3,912,400", "6,104,233"),
            ("2026-10-05", "CARD PAYMENT", "1,084,120", "", "5,020,113"),
            ("2026-10-11", "TRANSFER TO ***-**-**3381", "500,000", "", "4,520,113"),
            ("2026-10-18", "APARTMENT MGMT FEE", "198,700", "", "4,321,413"),
            ("2026-10-27", "INTEREST", "", "1,288", "4,322,701")]
    tr = "".join(f"<tr><td>{a}</td><td>{b}</td><td class='r'>{c}</td><td class='r'>{d}</td><td class='r'>{e}</td></tr>" for a, b, c, d, e in rows)
    p1 = page(f"""
<div class="en">
<div class="top"><span class="bank">UPS BANK</span><span>Customer Service 1588-0000 &nbsp;|&nbsp; www.upsbank.example</span></div>
<h1 style="letter-spacing:2px">ACCOUNT STATEMENT</h1><div class="sub">Statement Period: Oct 01, 2026 – Oct 31, 2026</div>
<table>
<tr><th>Account Holder</th><td>KIM M*** J***</td><th>Account No.</th><td>508-***-***819</td></tr>
<tr><th>Account Type</th><td>Ups Free Savings (KRW)</td><th>Branch</th><td>Daegu Buk Branch, 80 Daehak-ro, Buk-gu, Daegu</td></tr>
<tr><th>Opening Balance</th><td class="r">2,191,833</td><th>Closing Balance</th><td class="r">4,322,701</td></tr>
</table>
<h2>Transactions</h2>
<table><tr><th>Date</th><th>Description</th><th>Withdrawal</th><th>Deposit</th><th>Balance</th></tr>{tr}</table>
<p class="small">Personal identifiers on this statement have been masked by the issuing branch for external submission.<br>
Issued: Nov 03, 2026 &nbsp;|&nbsp; This statement is issued for reference only.</p>
</div>""")
    p2 = page("""
<div class="top"><span class="bank">업스은행</span><span>상품설명서 (고객 교부용)</span></div>
<h1>업스 자유적금 상품설명서</h1><div class="sub">이 설명서는 금융소비자보호법에 따라 상품의 주요 내용을 안내하기 위한 자료입니다.</div>
<table>
<tr><th>상품명</th><td>업스 자유적금</td><th>가입대상</th><td>실명의 개인 (1인 1계좌)</td></tr>
<tr><th>가입기간</th><td>6개월 이상 36개월 이하 (월 단위)</td><th>가입금액</th><td>월 1만원 이상 100만원 이하</td></tr>
<tr><th>기본금리</th><td>연 3.10% (12개월 기준, 세전)</td><th>우대금리</th><td>최고 연 0.80%p</td></tr>
<tr><th>이자지급</th><td colspan="3">만기일시지급식. 중도해지 시 납입기간별 중도해지이율 적용</td></tr>
<tr><th>예금자보호</th><td colspan="3">이 예금은 예금자보호법에 따라 원금과 소정의 이자를 합하여 1인당 최고 1억원까지 보호됩니다.</td></tr>
</table>
<h2>우대금리 조건</h2>
<table>
<tr><th>급여이체</th><td>3개월 이상 50만원 이상 급여 입금 시 연 0.40%p</td></tr>
<tr><th>카드실적</th><td>업스카드 월 30만원 이상 이용 시 연 0.20%p</td></tr>
<tr><th>마케팅동의</th><td>상품·서비스 안내 수신 동의 시 연 0.20%p</td></tr>
</table>
<h2>문의</h2>
<div class="box">업스은행 고객센터 1588-0000 (평일 09:00~18:00) &nbsp;|&nbsp; 본점: 대구광역시 중구 공평로 88</div>
<p class="small" style="margin-top:14px">상품설명서 관리번호 PRD-SAV-2026-11 &nbsp;|&nbsp; 준법감시인 심의필 제2026-0981호 (2026.10.15 ~ 2027.10.14)</p>
""")
    return [p1]


# ---------------------------------------------------------------- set03 (C)
def set03():
    p1 = page("""
<div class="top"><span class="bank">업스은행 기업금융부</span><span><span class="stamp">대외비</span></span></div>
<h1>기업 재무제표 요약</h1><div class="sub">여신심사 제출자료 — 2025 회계연도 (단위: 백만원)</div>
<table>
<tr><th>법인명</th><td>(주)대경정밀</td><th>사업자등록번호</th><td>504-81-23456</td></tr>
<tr><th>대표자</th><td>최도윤</td><th>업 종</th><td>자동차 부품 제조</td></tr>
<tr><th>본점 소재지</th><td colspan="3">경상북도 경산시 진량읍 공단4로 27</td></tr>
</table>
<h2>요약 재무상태표 · 손익계산서</h2>
<table>
<tr><th style="width:34%">계정</th><th>2024</th><th>2025</th><th>증감률</th></tr>
<tr><td>매출액</td><td class="r">38,420</td><td class="r">41,965</td><td class="r">+9.2%</td></tr>
<tr><td>영업이익</td><td class="r">2,105</td><td class="r">1,478</td><td class="r">-29.8%</td></tr>
<tr><td>당기순이익</td><td class="r">1,312</td><td class="r">706</td><td class="r">-46.2%</td></tr>
<tr><td>자산총계</td><td class="r">52,880</td><td class="r">57,214</td><td class="r">+8.2%</td></tr>
<tr><td>부채총계</td><td class="r">31,006</td><td class="r">36,950</td><td class="r">+19.2%</td></tr>
<tr><td>부채비율</td><td class="r">141.7%</td><td class="r">182.3%</td><td class="r">+40.6%p</td></tr>
</table>
<h2>심사역 메모</h2>
<div class="box">영업이익률 하락(5.5% → 3.5%)과 부채비율 상승은 설비 증설 차입금 영향. 운전자금 15억원 신규 신청 건으로 추가 담보 검토 필요.</div>
<p class="small" style="margin-top:14px">작성: 기업금융부 심사역 한지석 (2026-11-03) &nbsp;|&nbsp; 본 자료는 여신심사 목적 외 사용·외부 반출을 금합니다.</p>
""")
    p2 = page("""
<div class="top"><span class="bank">(주)대경정밀</span><span>여신심사 제출서류 — 주주명부 사본</span></div>
<h1>주 주 명 부</h1><div class="sub">기준일: 2026년 9월 30일 &nbsp;|&nbsp; 발행주식 총수 200,000주 (1주의 금액 5,000원)</div>
<table>
<tr><th style="width:5%">No</th><th style="width:15%">주주명</th><th style="width:20%">주민등록번호<br>(사업자등록번호)</th><th>주 소</th><th style="width:12%">소유주식</th><th style="width:9%">지분율</th></tr>
<tr><td>1</td><td>최도윤</td><td>710205-1462318</td><td>경상북도 경산시 대학로 33, 경산자이 105동 801호</td><td class="r">110,000</td><td class="r">55.0%</td></tr>
<tr><td>2</td><td>최서영</td><td>750811-2093814</td><td>경상북도 경산시 대학로 33, 경산자이 105동 801호</td><td class="r">40,000</td><td class="r">20.0%</td></tr>
<tr><td>3</td><td>(주)대경홀딩스</td><td>(504-86-11029)</td><td>대구광역시 수성구 달구벌대로 2450 (본점)</td><td class="r">50,000</td><td class="r">25.0%</td></tr>
<tr><td colspan="4" style="text-align:center">합 계</td><td class="r">200,000</td><td class="r">100.0%</td></tr>
</table>
<p style="text-align:center;margin-top:40px">위 주주명부는 당사 주주명부와 상위 없음을 확인합니다.</p>
<p style="text-align:center">2026년 10월 31일</p>
<p style="text-align:right;margin-right:40px">(주)대경정밀 대표이사 최도윤 <span class="seal">대경<br>정밀</span></p>
""")
    return [p1, p2]


# ---------------------------------------------------------------- set06 (F) 같은 계좌번호가 1쪽은 가려지고 2쪽은 그대로
def set06():
    def txrows(rows):
        return "".join(f"<tr><td>{a}</td><td>{b}</td><td class='r'>{c}</td><td class='r'>{d}</td><td class='r'>{e}</td></tr>" for a, b, c, d, e in rows)
    head = "<tr><th style='width:16%'>거래일</th><th>적요</th><th style='width:17%'>출금</th><th style='width:17%'>입금</th><th style='width:19%'>잔액</th></tr>"
    r1 = [("2026-10-01", "전월이월", "", "", "182,440,120"), ("2026-10-02", "매출대금 포스코엠텍", "", "48,200,000", "230,640,120"),
          ("2026-10-06", "원자재 대금 한국강재", "61,350,000", "", "169,290,120"), ("2026-10-10", "급여 일괄이체(38명)", "142,800,000", "", "26,490,120"),
          ("2026-10-14", "매출대금 동해조선", "", "95,000,000", "121,490,120"), ("2026-10-17", "부가세 납부", "18,904,300", "", "102,585,820")]
    r2 = [("2026-10-21", "운전자금 대출이자", "4,125,000", "", "98,460,820"), ("2026-10-24", "매출대금 포스코엠텍", "", "52,700,000", "151,160,820"),
          ("2026-10-27", "외주가공비 영일정공", "23,100,000", "", "128,060,820"), ("2026-10-31", "이자", "", "21,402", "128,082,222")]
    info = lambda acct: f"""<table>
<tr><th>예금주</th><td>(주)포항해양산업</td><th>사업자등록번호</th><td>506-81-55190</td></tr>
<tr><th>계좌번호</th><td>{acct}</td><th>조회기간</th><td>2026-10-01 ~ 2026-10-31</td></tr></table>"""
    p1 = page(f"""
<div class="top"><span class="bank">업스은행</span><span>거래내역 확인서 (외부 제출용) &nbsp;|&nbsp; 1 / 2쪽</span></div>
<h1>거래내역 확인서</h1><div class="sub">발급일 2026-11-04 &nbsp;|&nbsp; 발급번호 TX-2026-883104 &nbsp;|&nbsp; 제출처: 협력사 거래 등록</div>
{info("508-910-***317")}
<h2>거래 내역</h2><table>{head}{txrows(r1)}</table>
<p class="small">※ 외부 제출용으로 계좌번호 일부를 가렸습니다. (다음 쪽에 계속)</p>""")
    p2 = page(f"""
<div class="top"><span class="bank">업스은행</span><span>거래내역 확인서 (외부 제출용) &nbsp;|&nbsp; 2 / 2쪽</span></div>
{info("508-910-552317")}
<h2>거래 내역 (계속)</h2><table>{head}{txrows(r2)}</table>
<p style="text-align:center;margin-top:30px">위 거래내역이 당행 전산 기록과 같음을 확인합니다.</p>
<p style="text-align:right;margin-right:40px">업스은행 포항지점장 <span class="seal">업스<br>은행</span></p>""")
    return [p1, p2]


# ---------------------------------------------------------------- set07 (G) 이름은 가렸지만 조합으로 누구인지 짐작됨
def set07():
    return [page("""
<div class="top"><span class="bank">업스은행 소비자보호부</span><span>외부 기관 제출용 — 비식별 처리본</span></div>
<h1>민원 처리 결과 보고서</h1><div class="sub">민원번호 C-2026-04412 &nbsp;|&nbsp; 제출처: 금융소비자 보호 협의회(가상) &nbsp;|&nbsp; 작성일 2026-11-05</div>
<table>
<tr><th>민원인</th><td>이** (여)</td><th>연락처</th><td>010-****-****</td></tr>
<tr><th>접수 경로</th><td>업스뱅킹 앱 1:1 문의</td><th>접수일</th><td>2026-11-04</td></tr>
<tr><th>민원 유형</th><td colspan="3">비대면 대출 서류 제출 오류 및 처리 지연</td></tr>
</table>
<h2>민원 요지</h2>
<div class="box">민원인은 1995년생으로 울산 남구 (주)동해물류 물류운영팀에서 대리로 재직 중이며, 2026-11-03 21:47 업스뱅킹 앱으로 신분증 사본과 재직증명서를 올렸으나 "서류 판독 불가" 안내만 받고 대출 심사가 3일째 진행되지 않는다며 처리 지연과 안내 부족을 문제 삼음.</div>
<h2>처리 내용</h2>
<table>
<tr><th>원인</th><td>휴대폰 촬영 신분증 사본의 빛 번짐으로 자동 판독 실패, 재제출 안내 문자 미발송</td></tr>
<tr><th>조치</th><td>담당 심사역 배정 후 2026-11-05 유선 안내 완료, 선명한 사본 재제출 접수</td></tr>
<tr><th>재발 방지</th><td>판독 실패 시 재제출 안내 문자 자동 발송 기능 개선 (2026-12 반영 예정)</td></tr>
</table>
<p class="small" style="margin-top:14px">본 보고서는 개인정보 비식별 처리 후 외부 기관에 제출합니다. 작성: 소비자보호부 민원담당</p>
""")]


# ---------------------------------------------------------------- set04 (D)
def id_card_png():
    html = WORK / "idcard.html"
    html.write_text("""<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#6b5b4a;font-family:'Malgun Gothic';}
.card{position:absolute;left:90px;top:80px;width:820px;height:520px;border-radius:28px;
background:linear-gradient(135deg,#e9f1f7,#cfe0ec);box-shadow:0 8px 30px rgba(0,0,0,.5);padding:40px 46px;box-sizing:border-box}
.t{font-size:44px;font-weight:700;letter-spacing:10px;color:#203040}
.n{font-size:40px;margin-top:40px;color:#111}.r{font-size:40px;margin-top:14px;letter-spacing:3px}
.a{font-size:28px;margin-top:30px;line-height:42px;width:520px}
.ph{position:absolute;right:50px;top:120px;width:200px;height:250px;background:#9fb3c2;border-radius:6px}
.d{position:absolute;left:46px;bottom:40px;font-size:26px}
</style></head><body><div class="card"><div class="t">주민등록증</div>
<div class="n">이서윤 (李瑞允)</div><div class="r">950721-2481935</div>
<div class="a">울산광역시 남구 삼산로 274,<br>삼산타운 3동 702호</div><div class="ph"></div>
<div class="d">2021. 5. 14.  울산광역시 남구청장</div></div></body></html>""", encoding="utf-8")
    png = WORK / "idcard.png"
    edge_png(html, png, 1000, 700)
    img = Image.open(png).convert("RGB")
    # 휴대폰 촬영처럼: 기울임 + 강한 흐림 + 빛 번짐 + 노이즈 + 저해상도
    img = img.rotate(9, resample=Image.BICUBIC, expand=True, fillcolor=(70, 60, 50))
    img = img.resize((img.width // 5, img.height // 5)).resize((img.width, img.height))
    img = img.filter(ImageFilter.GaussianBlur(7))
    glare = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(glare)
    w, h = img.size
    d.ellipse((int(w * .18), int(h * .30), int(w * .78), int(h * .66)), fill=235)
    glare = glare.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(Image.new("RGB", img.size, (255, 255, 250)), img, glare)
    img = ImageEnhance.Brightness(img).enhance(0.85)
    rnd = random.Random(7)
    px = img.load()
    for _ in range(int(w * h * 0.04)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(-60, 60)
        r, g, b = px[x, y]
        px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=35)
    return base64.b64encode(buf.getvalue()).decode()


def set04():
    b64 = id_card_png()
    p1 = page(f"""
<div class="top"><span class="bank">업스은행</span><span>본인확인 서류 — 신분증 사본 (고객 모바일 제출)</span></div>
<div style="margin-top:20px;text-align:center"><img src="data:image/jpeg;base64,{b64}" style="width:100%;"></div>
<p class="small">제출 경로: 업스뱅킹 앱 서류 촬영 업로드 (2026-11-03 21:47)</p>
""")
    p2 = page("""
<div class="top"><span class="bank">(주)동해물류</span><span>제 2026-118 호</span></div>
<h1>재 직 증 명 서</h1>
<table style="margin-top:20px">
<tr><th>성 명</th><td>이서윤</td><th>생년월일</th><td>1995-07-21</td></tr>
<tr><th>소 속</th><td>물류운영팀</td><th>직 위</th><td>대리</td></tr>
<tr><th>재직기간</th><td colspan="3">2020-01-06 ~ 현재 (재직 중)</td></tr>
<tr><th>용 도</th><td colspan="3">금융기관 제출용</td></tr>
</table>
<p style="text-align:center;margin-top:50px;font-size:14px">위 사람은 당사에 재직하고 있음을 증명합니다.</p>
<p style="text-align:center;margin-top:20px">2026년 11월 03일</p>
<table style="margin-top:30px">
<tr><th>회사명</th><td>(주)동해물류</td><th>사업자등록번호</th><td>610-86-77412</td></tr>
<tr><th>소재지</th><td colspan="3">울산광역시 남구 장생포고래로 210 (회사 소재지)</td></tr>
<tr><th>대표이사</th><td colspan="3">윤재혁 <span class="seal">동해<br>물류</span></td></tr>
</table>
""")
    return [p1]


# ---------------------------------------------------------------- set05 (E)
def set05():
    p1 = page("""
<div class="top"><span class="bank">업스은행</span><span>업스CB 연계 조회 &nbsp;|&nbsp; 조회번호 Q-2026-110384</span></div>
<h1>개인신용정보 조회 결과서</h1><div class="sub">여신 심사용 내부 조회 결과 — 조회일 2026-11-04 10:12</div>
<table>
<tr><th>성 명</th><td>박지호</td><th>주민등록번호</th><td>880923-1******</td></tr>
<tr><th>조회 목적</th><td>신용대출 심사</td><th>조회자</th><td>여신담당 (사번 2110457)</td></tr>
</table>
<h2>신용평가 결과</h2>
<table>
<tr><th>신용평점</th><td style="font-size:15px;font-weight:700">712점 / 1000점</td><th>평점 구간</th><td>5구간</td></tr>
<tr><th>연체 이력</th><td>최근 5년 단기연체 1건 (2023-08, 12일, 해제)</td><th>현재 연체</th><td>없음</td></tr>
<tr><th>대출 잔액</th><td colspan="3">2개 기관, 합계 41,500,000원 (신용 18,000,000 / 자동차 23,500,000)</td></tr>
<tr><th>카드 이용</th><td colspan="3">보유 2매, 최근 3개월 월평균 이용액 1,320,000원</td></tr>
</table>
<p class="small" style="margin-top:14px">본 결과서는 신용정보법에 따른 개인신용정보로, 조회 목적 외 이용·제3자 제공을 금합니다.</p>
""")
    p2 = page("""
<div class="top"><span class="bank">업스카드</span><span><span class="stamp">개인정보 마스킹 완료</span></span></div>
<h1>신용카드 이용대금 명세서</h1><div class="sub">2026년 10월 이용분 (결제일 2026-11-14)</div>
<table>
<tr><th>회원명</th><td>박*호</td><th>카드번호</th><td>5310-****-****-4471</td></tr>
<tr><th>청구지 주소</th><td colspan="3">부산광역시 해운대구 ****로 ** (****동)</td></tr>
<tr><th>결제계좌</th><td>업스은행 ***-***-**5520</td><th>청구금액</th><td>1,284,300원</td></tr>
</table>
<h2>이용 내역</h2>
<table>
<tr><th style="width:16%">이용일</th><th>가맹점</th><th style="width:16%">이용금액</th><th style="width:34%">비고</th></tr>
<tr><td>10-03</td><td>업스마트 해운대점</td><td class="r">86,200</td><td></td></tr>
<tr><td>10-09</td><td>부산도시가스</td><td class="r">41,800</td><td>자동납부</td></tr>
<tr><td>10-15</td><td>AIRLINE TICKET (해외)</td><td class="r">612,000</td><td>해외승인 카드 5310-8821-4093-4471</td></tr>
<tr><td>10-21</td><td>해운대 문고</td><td class="r">38,500</td><td></td></tr>
<tr><td>10-28</td><td>업스주유소</td><td class="r">105,800</td><td></td></tr>
<tr><td>10-30</td><td>온라인쇼핑 결제</td><td class="r">400,000</td><td>할부 3개월</td></tr>
</table>
<p class="small" style="margin-top:14px">문의: 업스카드 고객센터 1588-0001</p>
""")
    return [p1, p2]


# ---------------------------------------------------------------- set08 (H) 외국인 고객 해외송금 신청서 (국·영문 병기)
def set08():
    return [page("""
<div class="top"><span class="bank">업스은행 <span class="en" style="font-size:12px">UPS BANK</span></span><span>[외환-03 서식] 접수번호 FX-2026-ULS-02281</span></div>
<h1 style="letter-spacing:2px">해외송금 신청서</h1><div class="sub en">Application for Outward Remittance</div>
<h2>1. 송금인 Remitter</h2>
<table>
<tr><th>성명 Name</th><td class="en">NGUYEN VAN HUNG</td><th>국적 Nationality</th><td>베트남 VIET NAM</td></tr>
<tr><th>외국인등록번호<br><span class="small en">Alien Reg. No.</span></th><td>930517-5281406</td><th>여권번호<br><span class="small en">Passport No.</span></th><td class="en">C4829157</td></tr>
<tr><th>주소 Address</th><td colspan="3">울산광역시 동구 방어진순환도로 1100, 한마음기숙사 B동 312호</td></tr>
<tr><th>휴대전화 Mobile</th><td>010-7714-2093</td><th>직장 Employer</th><td>(주)미포산업</td></tr>
<tr><th>출금계좌<br><span class="small en">Debit Account</span></th><td colspan="3">업스은행 512-308-660147 (본인 명의)</td></tr>
</table>
<h2>2. 수취인 Beneficiary</h2>
<table class="en">
<tr><th>Name</th><td>NGUYEN THI LAN</td><th>Relationship</th><td>Mother</td></tr>
<tr><th>Bank</th><td>Vietcombank, Nghe An Branch</td><th>SWIFT</th><td>BFTVVNVX</td></tr>
<tr><th>Account No.</th><td>0101-0004-38812</td><th>Country</th><td>VIET NAM</td></tr>
</table>
<h2>3. 송금 내용 Remittance</h2>
<table>
<tr><th>송금액 Amount</th><td>USD 1,200.00</td><th>송금 사유 Purpose</th><td>가족 생활비 Family support</td></tr>
<tr><th>수수료 Fee</th><td>KRW 15,000 (전신료 포함)</td><th>송금 방식</th><td>전신송금 (T/T)</td></tr>
</table>
<div class="box small" style="margin-top:8px">본인은 위 내용이 사실과 다름없음을 확인하며, 외국환거래법에 따른 송금 신청에 동의합니다. I confirm the above is true and correct.</div>
<p style="text-align:center;margin-top:24px">2026년 11월 04일 &nbsp; Date: Nov 04, 2026</p>
<p style="text-align:right;margin-right:40px">신청인 Signature : <span class="en">NGUYEN VAN HUNG</span> (서명)</p>
<p class="small">업스은행 울산동구지점 외환창구 &nbsp;|&nbsp; 고객센터 1588-0000</p>
""")]


# ---------------------------------------------------------------- set09 (I) 대출 상담 기록지 — 면허번호는 가렸고 연락처·주소·이메일은 그대로
def set09():
    return [page("""
<div class="top"><span class="bank">업스은행</span><span>상담 기록지 (내부 작성 → 대출모집법인 공유용)</span></div>
<h1>전세자금대출 상담 기록지</h1><div class="sub">상담일 2026-11-02 14:30 &nbsp;|&nbsp; 상담 채널: 영업점 방문 &nbsp;|&nbsp; 기록번호 CS-2026-50812</div>
<h2>1. 고객 정보</h2>
<table>
<tr><th>성 명</th><td>정유나</td><th>본인확인 수단</th><td>운전면허증 (28-**-******-**)</td></tr>
<tr><th>휴대전화</th><td>010-5530-8174</td><th>이메일</th><td>yuna.jung@example.net</td></tr>
<tr><th>현 거주지</th><td colspan="3">경상북도 구미시 인동가산로 9-3, 인동푸르지오 204동 1504호</td></tr>
</table>
<h2>2. 상담 내용</h2>
<table>
<tr><th>희망 상품</th><td>업스 전세자금대출 (보증기관 연계)</td><th>희망 금액</th><td>1억 5천만원 내외</td></tr>
<tr><th>임차 예정지</th><td colspan="3">구미시 옥계동 일대 아파트 (계약 전, 구체 주소 미정)</td></tr>
<tr><th>상담 요지</th><td colspan="3">전세 계약 전 한도 문의. 재직·소득 서류는 계약서 작성 후 제출 예정이라고 함. 보증기관별 금리 차이 설명 완료.</td></tr>
<tr><th>다음 할 일</th><td colspan="3">계약서 사본 접수 후 한도 산출 → 고객에게 문자 안내</td></tr>
</table>
<div class="box small" style="margin-top:10px">상담 기록은 대출 모집 업무 위탁 계약에 따라 대출모집법인과 공유합니다. 본인확인 수단 번호는 공유 전 가립니다.</div>
<p class="small" style="margin-top:16px">작성: 구미인동지점 여신상담 담당 &nbsp;|&nbsp; 지점 주소: 경상북도 구미시 인동중앙로 12 &nbsp;|&nbsp; 고객센터 1588-0000</p>
""")]


# ---------------------------------------------------------------- set10 (J) 공개 안내문을 스캔한 이미지 (약간 기울고 흐림, 판독은 가능)
def notice_png():
    html = WORK / "notice.html"
    html.write_text(html_doc([f"""<div style="padding:40px 50px">
<div class="top"><span class="bank">업스은행</span><span>영업점 게시용 안내문</span></div>
<h1>예금 금리 및 수수료 안내</h1><div class="sub">2026년 11월 1일부터 적용 (연 %, 세전)</div>
<h2>정기예금 · 적금 기본금리</h2>
<table>
<tr><th style="width:34%">상품</th><th>6개월</th><th>12개월</th><th>24개월</th></tr>
<tr><td>업스 정기예금</td><td class="r">2.85</td><td class="r">3.05</td><td class="r">3.10</td></tr>
<tr><td>업스 자유적금</td><td class="r">2.90</td><td class="r">3.10</td><td class="r">3.20</td></tr>
<tr><td>업스 청년도약적금</td><td class="r">-</td><td class="r">3.80</td><td class="r">4.00</td></tr>
</table>
<h2>주요 수수료</h2>
<table>
<tr><th style="width:34%">구분</th><th>영업점</th><th>업스뱅킹(앱·인터넷)</th></tr>
<tr><td>타행 이체 (10만원 이하)</td><td class="r">500원</td><td class="r">면제</td></tr>
<tr><td>타행 이체 (10만원 초과)</td><td class="r">1,000원</td><td class="r">면제</td></tr>
<tr><td>통장 재발행</td><td class="r">2,000원</td><td class="r">-</td></tr>
<tr><td>잔액증명서 발급</td><td class="r">2,000원</td><td class="r">1,000원</td></tr>
</table>
<div class="box" style="margin-top:12px">이 예금은 예금자보호법에 따라 원금과 소정의 이자를 합하여 1인당 최고 1억원까지 보호됩니다.<br>
문의: 업스은행 고객센터 1588-0000 (평일 09:00~18:00) &nbsp;|&nbsp; 본점: 대구광역시 중구 공평로 88</div>
<p class="small" style="margin-top:12px">게시번호 NTC-2026-1101 &nbsp;|&nbsp; 준법감시인 심의필 제2026-1033호</p>
</div>"""]), encoding="utf-8")
    png = WORK / "notice.png"
    edge_png(html, png, 1100, 1300)
    img = Image.open(png).convert("L")
    # 복합기 스캔처럼: 살짝 기울임 + 약한 흐림 + 회색 바탕 + 점 노이즈 (글자는 읽힘)
    img = img.rotate(-1.6, resample=Image.BICUBIC, expand=True, fillcolor=235)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img = ImageEnhance.Contrast(img).enhance(0.8)
    img = img.point(lambda v: int(v * 0.9 + 12))
    rnd = random.Random(11)
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.004)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        px[x, y] = rnd.randint(90, 170)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=55)
    return base64.b64encode(buf.getvalue()).decode()


def set10():
    b64 = notice_png()
    return [f'<div class="page"><img src="data:image/jpeg;base64,{b64}" style="width:100%;margin-top:6mm"><div class="foot">{FOOT}</div></div>']


SETS = [("set01", set01), ("set02", set02), ("set03", set03), ("set04", set04), ("set05", set05),
        ("set06", set06), ("set07", set07), ("set08", set08), ("set09", set09), ("set10", set10)]

if __name__ == "__main__":
    only = set(sys.argv[2:])  # 예: python build_docs.py 팀명 set08 set09 (비우면 전부)
    for name, fn in SETS:
        if only and name not in only:
            continue
        h = WORK / f"{name}.html"
        h.write_text(html_doc(fn()), encoding="utf-8")
        pdf = OUT / f"{TEAM}_미션2_{name}.pdf"
        edge_pdf(h, pdf)
        print("built", pdf.name)
