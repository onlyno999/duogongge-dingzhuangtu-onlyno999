#!/usr/bin/env python3
"""General voiceprint card builder (format fixed by user 2026-10-19, Diaoge style).
Usage: build_voiceprint_card.py ORIG_IMAGE AUDIO_WAV OUT_PNG TITLE LINE1 [LINE2]
- Original image pasted 1:1 untouched on top (verified after build by caller).
- Voiceprint strip appended at the very bottom only, scaled to image width
  (reference layout is 2048 wide with a 566 high strip).
- Waveform is drawn from AUDIO_WAV itself (min/max per column), never a stock shape.
- TITLE and transcript lines must come from that same track: language per the
  track's actual speech, transcript = recognized words. Do not copy labels
  from another person's example card.
"""
import sys, wave, contextlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

orig_path, audio_wav, out, title, line1 = sys.argv[1:6]
line2 = sys.argv[6] if len(sys.argv) > 6 else ''
FONT = '/home/hatch/workspace/fonts/NotoSansSC-var.ttf'

orig = Image.open(orig_path).convert('RGB')
W, H0 = orig.size
kx = W / 2048.0
# 1:1 with the Diaoge example: his photo area is 1482 high, strip 566.
# Strip height must follow the PHOTO height (566/1482), not the width —
# scaling by width made the strip ~33% of the finished card vs his 27.6%
# (user correction 2026-10-19: latter cards' voiceprint band was too wide).
STRIP_H = round(H0 * 566 / 1482)
ky = STRIP_H / 566.0
img = Image.new('RGB', (W, H0 + STRIP_H), (51, 55, 62))
img.paste(orig, (0, 0))
d = ImageDraw.Draw(img)
S = H0

def font(sz):
    f = ImageFont.truetype(FONT, round(sz * ky))
    try:
        f.set_variation_by_name('Regular')
    except Exception:
        pass
    return f

d.text((round(36 * kx), S + round(48 * ky)), title, font=font(52), fill=(245, 246, 248))

px0, py0, px1, py1 = round(32 * kx), S + round(148 * ky), W - round(32 * kx), S + round(414 * ky)
d.rectangle([px0, py0, px1, py1], fill=(28, 30, 35))
labels = ['800', '600', '400', '200', '0.0']
for i, lab in enumerate(labels):
    gy = py0 + round(12 * ky) + i * (py1 - py0 - round(24 * ky)) // 4
    d.line([px0, gy, px1, gy], fill=(78, 83, 92), width=1)
    d.text((px0 + round(4 * kx), gy - round(20 * ky)), lab, font=font(19), fill=(120, 126, 136))

with contextlib.closing(wave.open(audio_wav)) as w:
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
cols = px1 - px0
mid = (py0 + py1) / 2
amp = (py1 - py0) / 2 - round(6 * ky)
per = len(data) / cols
for x in range(cols):
    seg = data[int(x * per):int((x + 1) * per) + 1]
    if len(seg) == 0:
        continue
    lo, hi = float(seg.min()), float(seg.max())
    if hi - lo < 0.004:
        hi = lo + 0.004
    d.line([px0 + x, mid - hi * amp, px0 + x, mid - lo * amp], fill=(186, 197, 214), width=1)

tf = font(44)
lines = [l for l in (line1, line2) if l]
ty = S + STRIP_H - round(28 * ky) - len(lines) * round(56 * ky)
for l in lines:
    tw = d.textlength(l, font=tf)
    d.text((px1 - tw, ty), l, font=tf, fill=(245, 246, 248))
    ty += round(56 * ky)

img.save(out)
print('saved', out, img.size)
