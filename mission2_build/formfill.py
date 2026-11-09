# -*- coding: utf-8 -*-
"""국가법령정보센터 별지 서식(PDF)에 가상 값을 채우는 도우미."""
import io, random
from pathlib import Path
import fitz
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

ROOT = Path(__file__).resolve().parent
FORMS = ROOT / "forms"
FONT = r"C:\Windows\Fonts\malgun.ttf"
HAND = r"C:\Windows\Fonts\malgun.ttf"
INK = (0.08, 0.08, 0.35)  # 볼펜처럼 짙은 남색

FILES = {
    "f1": "f1_원천징수영수증.pdf", "f2": "f2_주식등변동상황명세서.pdf", "f3": "f3_사업자등록증.pdf",
    "f4": "f4_표준재무상태표.pdf", "f5": "f5_표준손익계산서.pdf", "f6": "f6_외국인등록사실증명.pdf",
    "f7": "f7_여권발급신청서.pdf", "f8": "f8_금융정보제공동의서.pdf",
}


def form_page(key, pno=0):
    """서식 PDF의 한 쪽만 담은 새 문서를 돌려준다."""
    src = fitz.open(FORMS / FILES[key])
    doc = fitz.open()
    doc.insert_pdf(src, from_page=pno, to_page=pno)
    page = doc[0]
    page.insert_font(fontname="mg", fontfile=FONT)
    return doc, page


def t(page, x, y, text, size=8.5, color=INK, right=False, center=False):
    """(x, y)를 글자 아래 기준선으로 보고 글자를 넣는다. right/center면 x를 오른쪽 끝/가운데로 본다."""
    if right or center:
        w = _len(text, size)
        x = x - w if right else x - w / 2
    page.insert_text((x, y), text, fontsize=size, fontname="mg", fontfile=FONT, color=color)


_F = fitz.Font(fontfile=FONT)


def _len(text, size):
    return _F.text_length(text, fontsize=size)


def boxes(page, x0, y, pitch, chars, size=9, color=INK):
    """한 칸에 한 글자씩 쓰는 서식용. x0는 첫 칸 가운데."""
    for i, ch in enumerate(chars):
        if ch != " ":
            t(page, x0 + i * pitch, y, ch, size=size, color=color, center=True)


def cover(page, rect, text=None, size=9, color=(0, 0, 0)):
    """서식의 ○○ 같은 자리표시를 흰 칸으로 덮고 값을 쓴다."""
    page.draw_rect(fitz.Rect(rect), color=None, fill=(1, 1, 1), overlay=True)
    if text:
        r = fitz.Rect(rect)
        t(page, r.x0 + 1, r.y1 - 2, text, size=size, color=color)


def stamp(page, cx, cy, text, r=16, color=(0.8, 0.1, 0.1)):
    """원형 직인(붉은 테두리 + 글자). 실제 인영처럼 약간 흐린 붉은색."""
    page.draw_circle((cx, cy), r, color=color, width=1.4, overlay=True)
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        t(page, cx, cy - (len(lines) - 1) * 4.5 + i * 9 + 3, ln, size=7, color=color, center=True)


def check(page, x, y, size=9):
    t(page, x, y, "V", size=size, color=INK)


def to_image_page(doc, dpi=150, rotate=0.0, blur=0.0, contrast=1.0, bright=1.0, noise=0.0, glare=None,
                  jpeg=60, seed=1, bg=(235, 235, 232), downscale=1):
    """채운 PDF를 스캔·촬영본처럼 이미지 한 쪽짜리 PDF로 바꾼다."""
    out = fitz.open()
    rnd = random.Random(seed)
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        if downscale > 1:
            w, h = img.size
            img = img.resize((w // downscale, h // downscale)).resize((w, h))
        if rotate:
            img = img.rotate(rotate, resample=Image.BICUBIC, expand=True, fillcolor=bg)
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur))
        if glare:
            gx0, gy0, gx1, gy1, a = glare
            w, h = img.size
            m = Image.new("L", img.size, 0)
            ImageDraw.Draw(m).ellipse((int(w * gx0), int(h * gy0), int(w * gx1), int(h * gy1)), fill=a)
            m = m.filter(ImageFilter.GaussianBlur(min(w, h) // 12))
            img = Image.composite(Image.new("RGB", img.size, (255, 255, 248)), img, m)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageEnhance.Brightness(img).enhance(bright)
        if noise:
            px = img.load()
            w, h = img.size
            for _ in range(int(w * h * noise)):
                x, y = rnd.randrange(w), rnd.randrange(h)
                v = rnd.randint(-70, 70)
                r, g, b = px[x, y]
                px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=jpeg)
        p = out.new_page(width=page.rect.width, height=page.rect.height)
        p.insert_image(p.rect, stream=buf.getvalue(), keep_proportion=False)
    return out


def join(docs):
    out = fitz.open()
    for d in docs:
        out.insert_pdf(d)
    return out
