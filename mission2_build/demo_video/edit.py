# Cut the Playwright recording by scene marks, speed up waits, overlay captions, add cards, concat.
import json, subprocess, sys, glob
from pathlib import Path

S = Path(__file__).resolve().parent / "work"  # pw/video, pw/marks.json, edit/ 가 들어가는 작업 폴더
FF = "ffmpeg"  # FFmpeg 실행 파일 경로
E = S / "edit"; TMP = E / "parts"; TMP.mkdir(parents=True, exist_ok=True)
src = sorted(glob.glob(str(S / "pw/video/*.webm")), key=lambda p: Path(p).stat().st_size)[-1]
M = dict(json.loads((S / "pw/marks.json").read_text(encoding="utf-8")))
OUT = Path(sys.argv[1])

def max_len(a, b, target):  # speed so that segment lasts at most `target` seconds
    return max(1.0, (M[b] - M[a]) / target)

# (start_mark, end_mark, speed, caption)
SEG = [
    ("table", "table_end", 1.0, "table"),
    ("table_end", "parse", max_len("table_end", "parse", 3), "table"),
    ("parse", "classify", 1.0, "parse"),
    ("classify", "extract", 1.0, "classify"),
    ("extract", "validate", 1.0, "extract"),
    ("validate", "judge", 1.0, "validate"),
    ("judge", "followup", 1.0, "judge"),
    ("followup", "studio_end", 1.0, "followup"),
    ("studio_end", "site", max_len("studio_end", "site", 3), "site"),
    ("site", "site_wait", 1.0, "site"),
    ("site_wait", "site_result", max_len("site_wait", "site_result", 4), "site_wait"),
    ("site_result", "mask", 1.0, "site_result"),
    ("mask", "masked_view", max_len("mask", "masked_view", 5), "mask"),
    ("masked_view", "end", 1.0, "masked_view"),
]

def run(args):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y"] + args, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stderr)

ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30"]
parts = []
def card(name, secs):
    o = TMP / f"{len(parts):02d}_{name}.mp4"
    run(["-loop", "1", "-t", str(secs), "-i", str(E / f"{name}.png"), "-vf", "fade=in:0:12,fade=out:st=%.2f:d=0.4" % (secs - 0.4)] + ENC + [str(o)])
    parts.append(o)

card("title", 4)
total = 4
for a, b, sp, cap in SEG:
    if a not in M or b not in M: print("skip", a, b); continue
    o = TMP / f"{len(parts):02d}_{a}.mp4"
    pad = 3 if a in ("extract", "judge", "followup", "site_result", "masked_view") else 0
    flt = f"[0:v]trim=start={M[a]}:end={M[b]},setpts=(PTS-STARTPTS)/{sp:.3f},fps=30,tpad=stop_mode=clone:stop_duration={pad},crop=1440:724:0:0,scale=1320:663:flags=lanczos[v];[1:v][v]overlay=60:24:shortest=1[o]"
    run(["-i", src, "-loop", "1", "-i", str(E / f"cap_{cap}.png"), "-filter_complex", flt, "-map", "[o]"] + ENC + [str(o)])
    parts.append(o); total += (M[b] - M[a]) / sp + pad
    print(f"{a:12s} {M[b]-M[a]:6.1f}s x{sp:4.1f} -> {(M[b]-M[a])/sp:5.1f}s")
card("end", 6); total += 6
lst = TMP / "list.txt"
lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(OUT)])
print("total ~%.1fs" % total, OUT)
