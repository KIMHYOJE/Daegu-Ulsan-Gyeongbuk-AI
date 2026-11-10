# Caption overlays (transparent 1440x900 PNG, lower-third card) and title/end cards. Modern light style.
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import sys

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H = 1440, 900
NOTO = "C:/Windows/Fonts/NotoSansKR-VF.ttf"

def F(size, w=400):
    f = ImageFont.truetype(NOTO, size); f.set_variation_by_axes([w]); return f

INK, SUB, MUTED = (17, 20, 45), (72, 78, 110), (120, 126, 155)
PURPLE, BLUE = (108, 92, 231), (37, 99, 235)
RISK = [("고위험", (220, 38, 38), (254, 226, 226)), ("중위험", (217, 119, 6), (254, 243, 199)),
        ("저위험", (22, 163, 74), (220, 252, 231)), ("검토 필요", (124, 58, 237), (237, 233, 254))]

# key: (pill, accent, title, sub)
CAPS = {
    "table":      ("STUDIO", PURPLE, "AI 워크플로우 '요미의 코딩'", "서류 묶음 20개를 한 워크플로우로 실행한 결과 표"),
    "parse":      ("STEP 1 · Parse", PURPLE, "OCR로 서류 묶음을 읽습니다", "set17 — 사업자등록증 + 표준손익계산서 + 대표자 금융정보 제공 동의서 (PDF 3쪽)"),
    "classify":   ("STEP 2 · Classify", PURPLE, "한 PDF를 서식별로 나눕니다", "법인 서류(1~2쪽) / 개인 서류(3쪽) — 나누지 않으면 서식마다 값이 섞임"),
    "extract":    ("STEP 3 · Extract", PURPLE, "칸별로 18개 항목을 뽑습니다", "가린 값(*)은 그대로 두고, 동의서 칸에 남은 주민등록번호를 찾음"),
    "validate":   ("STEP 4 · Validate", PURPLE, "못 읽은 서류를 걸러냅니다", "판독 상태 clear 필수 · 주민등록번호 신뢰도 0.8 이상"),
    "judge":      ("STEP 5 · 위험도_판정", (220, 38, 38), "판정 결과: 고위험", "검토 필요 → 고위험 → 중위험 → 저위험 순서 · 위험도·노출 항목·정보 주인·근거 4개 키"),
    "followup":   ("STEP 6 · 발송차단_보고", (220, 38, 38), "등급에 맞는 후속 문서를 씁니다", "노출 항목과 위치(문서·칸) 표 + 즉시 조치 · 보고 대상"),
    "site":       ("WEB", BLUE, "소개 사이트에서 바로 체험", "Upstage Document Parse + Solar 추출 → Studio와 같은 규칙으로 판정"),
    "site_wait":  ("WEB · 판정 중 (빠르게 감기)", BLUE, "set09 — 배우자 칸이 그대로 남은 동의서", "신청자 칸은 가렸지만 배우자 칸의 번호는 가리지 않음"),
    "site_result":("WEB · 결과", (220, 38, 38), "고위험 — 배우자 주민등록번호 · 휴대전화번호 노출", "항목별로 노출 / 가림 값을 근거와 함께 보여 줌"),
    "mask":       ("WEB · 가린 PDF", BLUE, "노출된 값만 검게 가립니다", "OCR 좌표로 값의 위치를 찾아 가린 PDF를 내려받음"),
    "masked_view":("WEB · 가린 PDF", BLUE, "가린 PDF 결과", "쪽을 그림으로 바꿔 가린 글자가 남지 않음"),
}

def tw(d, t, f): return d.textlength(t, font=f)

# Video frame: source cropped to 1440x724 (Studio recording has grey padding below y=725), scaled into BOX.
BOX = (60, 24, 1380, 687)  # x0, y0, x1, y1  -> 1320x663 (1440:724 aspect)

def caption(key, pill, accent, title, sub):
    im = background(); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = BOX
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((x0, y0 + 8, x1, y1 + 8), 16, fill=(30, 30, 70, 70))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), 14, fill=(255, 255, 255), outline=(222, 224, 240), width=2)
    # caption strip below the frame
    fp, ft, fs = F(17, 700), F(32, 700), F(21, 400)
    cy = y1 + 30
    pw = tw(d, pill, fp) + 28
    d.rounded_rectangle((x0, cy, x0 + pw, cy + 32), 16, fill=accent + (255,))
    d.text((x0 + 14, cy + 3), pill, font=fp, fill=(255, 255, 255))
    d.text((x0 + pw + 18, cy - 6), title, font=ft, fill=INK)
    d.text((x0, cy + 52), sub, font=fs, fill=SUB)
    im.convert("RGB").save(OUT / f"cap_{key}.png")

def background():
    im = Image.new("RGB", (W, H), (248, 248, 253))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse((880, -260, 1640, 500), fill=(124, 108, 255, 120))
    g.ellipse((1050, 420, 1700, 1080), fill=(96, 165, 250, 90))
    g.ellipse((-300, 600, 400, 1200), fill=(196, 181, 253, 70))
    im = Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 48):  # faint dot grid
        for y in range(0, H, 48):
            d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(200, 202, 225, 120))
    return im

def chip(d, x, y, text, fg, bg, f):
    w = tw(d, text, f) + 36
    d.rounded_rectangle((x, y, x + w, y + 44), 22, fill=bg); d.text((x + 18, y + 6), text, font=f, fill=fg)
    return x + w + 12

def title_card():
    im = background(); d = ImageDraw.Draw(im)
    x = 120
    f = F(20, 700); w = tw(d, "IM뱅크 지정주제 · 요미의 코딩", f) + 36
    d.rounded_rectangle((x, 220, x + w, 260), 20, fill=(255, 255, 255), outline=(220, 216, 250), width=2)
    d.text((x + 18, 226), "IM뱅크 지정주제 · 요미의 코딩", font=f, fill=PURPLE)
    d.text((x, 300), "금융 서류 외부 발송 전,", font=F(64, 800), fill=INK)
    d.text((x, 390), "민감정보 자동 식별과 위험도 등급화", font=F(64, 800), fill=INK)
    d.text((x, 498), "Upstage AI Studio 워크플로우 데모 — 서류 입력부터 판정 · 후속 조치까지", font=F(26, 400), fill=SUB)
    cx = x
    for t, fg, bg in RISK: cx = chip(d, cx, 580, t, fg, bg, F(20, 700))
    d.text((x, 780), "Upstage Studio · Document Parse · Solar", font=F(18, 500), fill=MUTED)
    im.convert("RGB").save(OUT / "title.png")

def stat(d, x, y, big, small, color):
    d.rounded_rectangle((x, y, x + 360, y + 170), 24, fill=(255, 255, 255), outline=(228, 230, 242), width=2)
    d.text((x + 30, y + 24), big, font=F(54, 800), fill=color)
    d.text((x + 30, y + 112), small, font=F(20, 500), fill=SUB)

def end_card():
    im = background(); d = ImageDraw.Draw(im)
    x = 120
    d.text((x, 150), "결과", font=F(22, 700), fill=PURPLE)
    d.text((x, 190), "가려지지 않은 번호를, 보내기 전에 찾습니다", font=F(48, 800), fill=INK)
    stat(d, x, 300, "20개", "서류 묶음 · 법정 서식 8종", INK)
    stat(d, x + 390, 300, "19 / 20", "Studio 워크플로우 정답 일치", PURPLE)
    stat(d, x + 780, 300, "20 / 20", "소개 사이트 정답 일치", BLUE)
    cx = x
    for (t, fg, bg), a in zip(RISK, ["발송 차단", "마스킹 요청", "발송 승인", "담당자 확인"]):
        cx = chip(d, cx, 530, f"{t} → {a}", fg, bg, F(19, 700))
    d.text((x, 690), "github.com/KIMHYOJE/Daegu-Ulsan-Gyeongbuk-AI", font=F(22, 500), fill=SUB)
    d.text((x, 728), "yomicoding-site.vercel.app", font=F(22, 500), fill=SUB)
    d.text((x, 790), "요미의 코딩 · 2026 대구·울산·경북 AI Agent 해커톤", font=F(18, 500), fill=MUTED)
    im.convert("RGB").save(OUT / "end.png")

for k, v in CAPS.items(): caption(k, *v)
title_card(); end_card()
print("ok")
