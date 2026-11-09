# -*- coding: utf-8 -*-
"""최종 제출 데이터셋: 법정 별지 서식에 가상 값을 채워 케이스별 PDF를 만든다.
사용법: python fill_cases.py <팀명> [setNN ...]
"""
import sys
from pathlib import Path
import fitz
from formfill import form_page, t, boxes, cover, stamp, check, to_image_page, join, INK

TEAM = sys.argv[1] if len(sys.argv) > 1 else "팀명"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "최종제출_제출물"
OUT.mkdir(exist_ok=True)


# ------------------------------------------------------------------ 서식별 채우기
def f6_foreign(p):
    """외국인등록 사실증명. p: dict"""
    doc, pg = form_page("f6")
    t(pg, 100, 133, p["serial"])
    t(pg, 330, 133, p["issued"])
    t(pg, 380, 160, p["arc"], size=9)
    t(pg, 250, 186, p["name"], size=9)
    t(pg, 205, 241, p["sex"])
    t(pg, 318, 241, p["birth"])
    t(pg, 456, 241, p["passport"], size=8.5)
    t(pg, 262, 257, p["country"])
    t(pg, 492, 257, p["status"])
    t(pg, 262, 280, p["period"], size=7.5)
    t(pg, 493, 280, p["regdate"], size=7.5)
    t(pg, 240, 303, p["address"])
    t(pg, 145, 355, "금융기관 제출용")
    t(pg, 400, 363, p["name_kr"], size=8)
    for i, (rel, nm, sx, arc) in enumerate(p.get("family", [])):
        y = 582 + i * 12
        t(pg, 160, y, rel, size=8); t(pg, 235, y, nm, size=8); t(pg, 360, y, sx, size=8); t(pg, 430, y, arc, size=8)
    y, m, d = p["issued"].split("-")
    t(pg, 256, 694, y); t(pg, 330, 694, m); t(pg, 402, 694, d)
    t(pg, 210, 712, p["officer"], size=8)
    t(pg, 420, 712, "1345", size=8)
    return doc


def f3_bizreg(p):
    """사업자등록증."""
    doc, pg = form_page("f3")
    t(pg, 248, 152, p["kind"], size=10, color=(0, 0, 0))
    t(pg, 222, 172, p["bizno"], size=11, color=(0, 0, 0))
    t(pg, 133, 206, p["company"], size=10, color=(0, 0, 0))
    t(pg, 412, 206, p["ceo"], size=10, color=(0, 0, 0))
    yy, mm, dd = p["opened"].split("-")
    t(pg, 194, 245, yy, size=10, color=(0, 0, 0)); t(pg, 252, 245, mm, size=10, color=(0, 0, 0)); t(pg, 300, 245, dd, size=10, color=(0, 0, 0))
    t(pg, 432, 245, p["ceo_birth"], size=10, color=(0, 0, 0))
    t(pg, 170, 283, p["site"], size=10, color=(0, 0, 0))
    t(pg, 238, 324, p["biz_type"], size=9, color=(0, 0, 0))
    t(pg, 343, 324, p["biz_item"], size=9, color=(0, 0, 0))
    t(pg, 170, 368, p.get("reason", "신규"), size=10, color=(0, 0, 0))
    yy, mm, dd = p["issued"].split("-")
    t(pg, 330, 611, yy, size=10, color=(0, 0, 0)); t(pg, 410, 611, mm, size=10, color=(0, 0, 0)); t(pg, 480, 611, dd, size=10, color=(0, 0, 0))
    for r in pg.search_for("○○세무서장"):
        cover(pg, (r.x0 - 2, r.y0 - 1, r.x1 + 1, r.y1 + 1))
        t(pg, r.x1, r.y1 - 2, p["office"] + "세무서장", size=15, color=(0, 0, 0), right=True)
    t(pg, 372, 493, "V", size=9, color=(0, 0, 0))  # 사업자 단위 과세: 부
    return doc


def f1_wage(p):
    """근로소득 원천징수영수증 1쪽."""
    doc, pg = form_page("f1")
    check(pg, 121, 88)  # [V]근로소득 원천징수영수증
    check(pg, 124, 124)  # [V]소득자 보관용
    t(pg, 170, 163, p["company"]); t(pg, 400, 163, p["ceo"])
    t(pg, 170, 175, p["bizno"])
    t(pg, 170, 198, p["company_addr"], size=8)
    t(pg, 170, 210, p["name"]); t(pg, 440, 210, p["rrn"], size=8.5)
    t(pg, 170, 222, p["address"], size=8)
    t(pg, 172, 251, p["company"], size=7.5)
    t(pg, 172, 267, p["bizno"], size=7.5)
    t(pg, 170, 283, p["period"], size=6.2)
    for label_y, key in ((313, "salary"), (328, "bonus"), (422, "total")):
        t(pg, 236, label_y, p[key], size=7.5, right=True)
        t(pg, 528, label_y, p[key], size=7.5, right=True)
    t(pg, 345, 626, p["tax"], size=7.5, right=True)
    t(pg, 440, 626, p["local_tax"], size=7.5, right=True)
    yy, mm, dd = p["issued"].split("-")
    t(pg, 427, 745, yy, size=8, right=True); t(pg, 459, 745, mm, size=8, right=True); t(pg, 490, 745, dd, size=8, right=True)
    t(pg, 300, 757, p["company"] + "  대표 " + p["ceo"], size=8)
    stamp(pg, 470, 752, p["company"][:2] + "\n" + p["company"][2:4], r=12)
    if p.get("masked_stamp"):
        t(pg, 380, 52, "[개인정보 마스킹 처리본]", size=9, color=(0.75, 0.1, 0.1))
    return doc


def f2_shares(p):
    """주식등변동상황명세서 1쪽 (A3 가로)."""
    doc, pg = form_page("f2")
    t(pg, 224, 146, p["company"]); t(pg, 595, 146, p["bizno"]); t(pg, 978, 146, p["ceo"])
    cover(pg, (948, 156, 1124, 166), p["fy"], size=8, color=INK)
    t(pg, 160, 266, "보통주", size=7); t(pg, 262, 266, p["shares_total"], size=7, right=True)
    t(pg, 344, 266, "5,000", size=7, right=True); t(pg, 540, 266, p["capital"], size=7, right=True)
    t(pg, 330, 441, p["shares_total"], size=6.5, right=False)
    t(pg, 368, 441, "100.00", size=6.5)
    t(pg, 968, 441, p["shares_total"], size=6.5); t(pg, 1016, 441, "100.00", size=6.5)
    for i, s in enumerate(p["holders"]):
        y = 480 + i * 16.8
        t(pg, 96, y, s["kind"], size=6.5); t(pg, 144, y, s["name"], size=6.5)
        t(pg, 187, y, s["id"], size=6.3); t(pg, 256, y, "대한민국", size=6.5); t(pg, 304, y, "KR", size=6.5)
        t(pg, 362, y, s["shares"], size=6.5, right=True); t(pg, 398, y, s["pct"], size=6.5, right=True)
        t(pg, 1010, y, s["shares"], size=6.5, right=True); t(pg, 1060, y, s["pct"], size=6.5, right=True)
        t(pg, 1090, y, s["rel"], size=6.5)
    t(pg, 735, 780, p["ceo"], size=9)
    stamp(pg, 790, 776, p["company"][3:5] + "\n" + p["company"][5:7], r=13)
    return doc


def f4_balance(p):
    """표준재무상태표 1쪽."""
    doc, pg = form_page("f4")
    t(pg, 178, 131, p["bizno"], size=7.5); t(pg, 178, 144, p["corpno"], size=7.5)
    t(pg, 330, 141, p["company"], size=8)
    cover(pg, (440, 127, 512, 139), p["asof"] + " 현재", size=7.5, color=INK)
    rows_l = {"Ⅰ.유동자산": (164, 175), "(1)당좌자산": (176, 187), "1.현금": (189, 199), "2.단기예금": (201, 212),
              "4.매출채권": (263, 273), "(2)재고자산": (546, 556), "1.상품": (558, 569), "2.제품": (570, 581)}
    rows_r = {"Ⅱ.비유동자산": (275, 286), "(1)투자자산": (287, 298), "(2)유형자산": (546, 556), "1.토지": (558, 569),
              "2.건물": (595, 606), "4.기계장치": (693, 704)}
    for k, v in p["left"].items():
        t(pg, 284, rows_l[k][1] - 2, v, size=7, right=True)
    for k, v in p["right"].items():
        t(pg, 530, rows_r[k][1] - 2, v, size=7, right=True)
    return doc


def f5_income(p):
    """표준손익계산서 1쪽."""
    doc, pg = form_page("f5")
    (y1, m1, d1), (y2, m2, d2) = p["from"].split("-"), p["to"].split("-")
    for (yy, mm, dd), base in (((y1, m1, d1), 100), ((y2, m2, d2), 116)):
        t(pg, 75, base, yy, size=7.5, right=True); t(pg, 97, base, mm, size=7.5, right=True); t(pg, 119, base, dd, size=7.5, right=True)
    t(pg, 470, 100, p["company"], size=8); t(pg, 462, 116, p["bizno"], size=7.5)
    rows_l = {"Ⅰ.매출액": 160, "1.상품매출": 171, "2.제품매출": 207, "Ⅱ.매출원가": 455, "(2)제조원가": 537}
    rows_r = {"Ⅲ.매출총손익": 230, "Ⅳ.판매비와관리비": 242, "1.급여": 254, "가.임원급여": 266, "나.직원급여": 278,
              "3.보험료": 372, "4.복리후생비": 384, "6.임차료": 407}
    for k, v in p["left"].items():
        t(pg, 284, rows_l[k] - 2, v, size=7, right=True)
    for k, v in p["right"].items():
        t(pg, 530, rows_r[k] - 2, v, size=7, right=True)
    return doc


R6 = [246, 268, 290, 312.5, 335, 357]           # 여권신청서 주민번호 앞 6칸 가운데
R7 = [401, 423.6, 446, 468, 490, 512, 534]       # 뒤 7칸
PH = R6 + [379] + R7[:6]                          # 연락처 13칸 (숫자만)


def f7_passport(p):
    """여권발급신청서 1쪽."""
    doc, pg = form_page("f7")
    check(pg, 141, 114); check(pg, 141, 135)          # 일반 / 10년
    boxes(pg, 249, 187, 30.9, p["name"], size=11)
    a, b = p["rrn"].split("-")
    for x, ch in zip(R6, a): t(pg, x, 211, ch, size=10, center=True)
    for x, ch in zip(R7, b): t(pg, x, 211, ch, size=10, center=True)
    for x, ch in zip(PH, p["phone"].replace("-", "")): t(pg, x, 235, ch, size=10, center=True)
    boxes(pg, 246.7, 274, 24.05, p["em_name"], size=10)
    t(pg, 470, 274, p["em_rel"], size=9)
    for x, ch in zip(PH, p["em_phone"].replace("-", "")): t(pg, x, 302, ch, size=10, center=True)
    boxes(pg, 146, 349, 24.05, p["rom_sur"], size=10)
    boxes(pg, 146, 381, 24.05, p["rom_given"], size=10)
    yy, mm, dd = p["date"].split("-")
    t(pg, 452, 549, yy, size=8.5, right=True); t(pg, 488, 549, mm, size=8.5, right=True); t(pg, 524, 549, dd, size=8.5, right=True)
    t(pg, 420, 564, p["name"], size=10)
    t(pg, 426, 655, p["name"], size=10)
    return doc


F8_R6 = [337.5, 363, 388.5, 414, 439.5, 465]
F8_R7 = [337.5, 363, 388.5, 414, 439.5, 465, 492]
F8_S6 = [209.5, 233.5, 258, 282.5, 307, 331]
F8_S7 = F8_S6 + [355.5]


def f8_consent(p):
    """금융정보 등(금융·신용·보험정보) 제공 동의서 1쪽."""
    doc, pg = form_page("f8")
    t(pg, 200, 153, p["name"], size=11)
    a, b = p["rrn"].split("-")
    for x, ch in zip(F8_R6, a): t(pg, x, 141, ch, size=10, center=True)
    for x, ch in zip(F8_R7, b): t(pg, x, 162, ch, size=10, center=True)
    t(pg, 130, 185, p["address"], size=9)
    for i, m in enumerate(p["members"]):
        dy = i * 65
        t(pg, 102, 305 + dy, m["rel"], size=9, center=True)
        t(pg, 158, 305 + dy, m["name"], size=9, center=True)
        a, b = m["rrn"].split("-")
        for x, ch in zip(F8_S6, a): t(pg, x, 290 + dy, ch, size=9, center=True)
        for x, ch in zip(F8_S7, b): t(pg, x, 306 + dy, ch, size=9, center=True)
        t(pg, 214, 322 + dy, m["phone"], size=8)
        t(pg, 404, 305 + dy, m["name"] + " (서명)", size=8, center=True)
    yy, mm, dd = p["date"].split("-")
    t(pg, 214, 773, " ".join(yy), size=10); t(pg, 296, 773, " ".join(mm), size=10); t(pg, 348, 773, " ".join(dd), size=10)
    return doc


SETS = {}

# ------------------------------------------------------------------ 케이스 정의 (가상 값: 번호에 0을 많이 넣어 가상임을 드러냄)
CO1 = dict(company="(주)가상테크", ceo="정가상", bizno="000-81-00123", company_addr="대구광역시 북구 가상로 10 (본사)")
CO2 = dict(company="(주)가상정밀", bizno="000-81-00456", corpno="000000-0000456", ceo="최가상")
CO3 = dict(company="(주)가상물산", bizno="000-81-00789", corpno="000000-0000789", ceo="윤가상")
CO4 = dict(company="(주)가상해운", bizno="000-81-00321", corpno="000000-0000321", ceo="강가상")

BS2 = dict(left={"Ⅰ.유동자산": "21,480,500,000", "(1)당좌자산": "14,210,300,000", "1.현금": "3,105,000,000",
                 "4.매출채권": "9,880,200,000", "(2)재고자산": "7,270,200,000", "2.제품": "5,120,000,000"},
           right={"Ⅱ.비유동자산": "35,733,500,000", "(2)유형자산": "31,902,000,000", "1.토지": "12,400,000,000",
                  "2.건물": "9,850,000,000", "4.기계장치": "9,652,000,000"})
BS3 = dict(left={"Ⅰ.유동자산": "8,215,000,000", "(1)당좌자산": "6,034,700,000", "1.현금": "1,212,300,000",
                 "2.단기예금": "1,500,000,000", "4.매출채권": "3,322,400,000", "(2)재고자산": "2,180,300,000",
                 "1.상품": "2,180,300,000"},
           right={"Ⅱ.비유동자산": "4,870,600,000", "(1)투자자산": "650,000,000", "(2)유형자산": "4,220,600,000",
                  "1.토지": "2,100,000,000", "2.건물": "2,120,600,000"})
IS2 = dict(left={"Ⅰ.매출액": "41,965,000,000", "2.제품매출": "41,965,000,000", "Ⅱ.매출원가": "35,108,000,000"},
           right={"Ⅲ.매출총손익": "6,857,000,000", "Ⅳ.판매비와관리비": "5,379,000,000", "1.급여": "2,410,000,000",
                  "가.임원급여": "420,000,000", "나.직원급여": "1,990,000,000", "3.보험료": "212,000,000",
                  "4.복리후생비": "388,000,000", "6.임차료": "96,000,000"})
IS4 = dict(left={"Ⅰ.매출액": "18,402,000,000", "1.상품매출": "18,402,000,000", "Ⅱ.매출원가": "15,770,000,000"},
           right={"Ⅲ.매출총손익": "2,632,000,000", "Ⅳ.판매비와관리비": "1,904,000,000", "1.급여": "1,120,000,000",
                  "가.임원급여": "210,000,000", "나.직원급여": "910,000,000", "6.임차료": "144,000,000"})


def holders(masked):
    m = (lambda s: s[:8] + "******") if masked else (lambda s: s)
    return [dict(kind="개인", name="최가상", id=m("710205-1000025"), shares="110,000", pct="55.00", rel="00"),
            dict(kind="개인", name="최배우", id=m("750811-2000036"), shares="40,000", pct="20.00", rel="01"),
            dict(kind="법인", name="(주)가상홀딩스", id="000-86-00789", shares="50,000", pct="25.00", rel="10")]


def shares(co, masked):
    return f2_shares(dict(company=co["company"], bizno=co["bizno"], ceo=co["ceo"], fy="2025.01.01 ~ 2025.12.31",
                          shares_total="200,000", capital="1,000,000,000", holders=holders(masked)))


def wage(**kw):
    base = dict(CO1, period="2025.01.01~2025.12.31", issued="2026-02-27")
    base.update(kw)
    return f1_wage(base)


ARC = dict(serial="2026-0012345", issued="2026-11-03", arc="930517-5000041", name="NGUYEN VAN AN",
           name_kr="NGUYEN VAN AN", sex="M", birth="1993-05-17", passport="C0000123", country="VIET NAM",
           status="E-9", period="2025-03-02 ~ 2028-03-01", regdate="2025-03-20",
           address="울산광역시 동구 가상로 100, 기숙사 B동 312호", officer="출입국민원 담당 김가상",
           family=[("배우자 Spouse", "TRAN THI MAI", "F", "950810-6000052")])
ARC2 = dict(ARC, serial="2026-0020871", arc="910224-6000074", name="SANTOS MARIA LUZ", name_kr="SANTOS MARIA LUZ",
            sex="F", birth="1991-02-24", passport="P0000456", country="PHILIPPINES", status="F-6",
            period="2024-08-01 ~ 2027-07-31", regdate="2024-08-14", address="경상북도 경산시 가상로 21, 302호",
            family=[("배우자 Spouse", "박가상", "M", "-")])

SETS = {
    "set01": lambda: join([wage(name="김가상", rrn="900101-1000017", address="대구광역시 수성구 가상로 101, 101동 1001호",
                                salary="48,000,000", bonus="6,000,000", total="54,000,000", tax="2,104,000", local_tax="210,400"),
                           f8_consent(dict(name="김가상", rrn="900101-1000017", address="대구광역시 수성구 가상로 101, 101동 1001호",
                                           members=[dict(rel="본인", name="김가상", rrn="900101-1000017", phone="010-0000-2847")],
                                           date="2026-11-02"))]),
    "set02": lambda: wage(name="송가상", rrn="920202-2******", address="대구광역시 ○○구 ****로 **, ***동 ***호",
                          salary="39,600,000", bonus="3,300,000", total="42,900,000", tax="1,212,000", local_tax="121,200",
                          masked_stamp=True),
    "set03": lambda: join([f4_balance(dict(CO2, asof="2025. 12. 31.", **BS2)),
                           f5_income(dict(CO2, **{"from": "2025-01-01", "to": "2025-12-31"}, **IS2)),
                           shares(CO2, masked=False)]),
    "set04": lambda: join([f4_balance(dict(CO3, asof="2025. 12. 31.", **BS3)),
                           f3_bizreg(dict(kind="법인과세자", bizno=CO3["bizno"], company=CO3["company"], ceo=CO3["ceo"],
                                          opened="2012-06-01", ceo_birth="1969-09-30", site="대구광역시 달서구 가상공단로 33",
                                          biz_type="도매업", biz_item="산업용 기계", issued="2012-06-01", office="서대구"))]),
    "set05": lambda: f3_bizreg(dict(kind="개인과세자", bizno="000-00-00123", company="가상정밀", ceo="박가상",
                                    opened="2019-03-04", ceo_birth="1978-04-12", site="경상북도 구미시 가상산단로 7",
                                    biz_type="제조업", biz_item="금속가공", issued="2019-03-04", office="구미")),
    "set06": lambda: f6_foreign(ARC),
    "set07": lambda: to_image_page(f6_foreign(ARC2), dpi=110, rotate=8, blur=3.2, downscale=3, contrast=0.75,
                                   bright=0.85, noise=0.05, glare=(0.15, 0.12, 0.85, 0.42, 235), jpeg=35, seed=7,
                                   bg=(92, 80, 66)),
    "set08": lambda: to_image_page(f7_passport(dict(name="이가상", rrn="880512-2000048", phone="010-0000-4821",
                                                     em_name="이부모", em_rel="부", em_phone="010-0000-7710",
                                                     rom_sur="LEE", rom_given="GASANG", date="2026-11-02")),
                                   dpi=150, rotate=-1.3, blur=0.5, contrast=0.9, noise=0.003, jpeg=60, seed=8),
    "set09": lambda: f8_consent(dict(name="한가상", rrn="850315-1******", address="경상북도 포항시 남구 ****로 **, ***동 ****호",
                                     members=[dict(rel="본인", name="한가상", rrn="850315-1******", phone="010-****-3392"),
                                              dict(rel="배우자", name="오가상", rrn="870722-2000063", phone="010-0000-5518")],
                                     date="2026-11-04")),
    "set10": lambda: join([f7_passport(dict(name="박가상", rrn="890630-1000082", phone="010-0000-6604",
                                            em_name="SANTOS", em_rel="배우자", em_phone="010-0000-1290",
                                            rom_sur="PARK", rom_given="GASANG", date="2026-11-03")),
                           f6_foreign(ARC2)]),
    "set11": lambda: shares(CO2, masked=True),
    "set12": lambda: to_image_page(f8_consent(dict(name="문가상", rrn="830909-2000091", address="대구광역시 동구 가상로 77, 5층",
                                                   members=[dict(rel="본인", name="문가상", rrn="830909-2000091", phone="010-0000-8203")],
                                                   date="2026-11-05")),
                                   dpi=100, rotate=-4, blur=2.6, downscale=3, contrast=0.7, bright=0.9, noise=0.04,
                                   glare=(0.45, 0.08, 1.0, 0.45, 240), jpeg=35, seed=12, bg=(120, 118, 110)),
    "set13": lambda: join([f5_income(dict(CO4, **{"from": "2025-01-01", "to": "2025-12-31"}, **IS4)),
                           shares(CO4, masked=True),
                           f3_bizreg(dict(kind="법인과세자", bizno=CO4["bizno"], company=CO4["company"], ceo=CO4["ceo"],
                                          opened="2008-02-11", ceo_birth="1965-01-20", site="경상북도 포항시 북구 가상항구로 5",
                                          biz_type="운수업", biz_item="연안 화물운송", issued="2008-02-11", office="포항"))]),
    "set14": lambda: wage(company="(주)가상유통", ceo="서가상", bizno="000-81-00654", company_addr="울산광역시 남구 가상대로 200",
                          name="임가상", rrn="950721-2000105", address="울산광역시 남구 가상로 274, 3동 702호",
                          salary="31,200,000", bonus="2,400,000", total="33,600,000", tax="604,000", local_tax="60,400"),
}

if __name__ == "__main__":
    only = set(sys.argv[2:])
    for name, fn in SETS.items():
        if only and name not in only:
            continue
        doc = fn()
        doc.save(OUT / f"{TEAM}_최종제출_{name}.pdf", garbage=3, deflate=True)
        print(name, doc.page_count)
