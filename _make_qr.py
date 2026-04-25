"""
Generate a cute QR code with 🥊 emoji at center for the punchpunchpunch site.
- Rounded module dots (kawaii pixel grid)
- White/yellow/red layered emoji badge at center
- High error correction (H, ~30%) so emoji overlay stays scannable
"""
from PIL import Image, ImageDraw, ImageFont
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import math

URL = 'https://ta1m1kam.github.io/punchpunchpunch/'
EMOJI = '🥊'
RED = (255, 43, 59, 255)
YELLOW = (255, 217, 26, 255)
INK = (10, 10, 15, 255)
WHITE = (255, 255, 255, 255)

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=30,
    border=3,
)
qr.add_data(URL)
qr.make(fit=True)

img = qr.make_image(
    image_factory=StyledPilImage,
    module_drawer=RoundedModuleDrawer(radius_ratio=1.0),
    color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=RED[:3]),
).convert('RGBA')

W, H = img.size
cx, cy = W // 2, H // 2

# Comic-style radial burst behind the emoji badge
burst_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
bdraw = ImageDraw.Draw(burst_layer)
burst_r_outer = int(W * 0.20)
burst_r_inner = int(W * 0.13)
spokes = 16
for i in range(spokes):
    a = (i / spokes) * 2 * math.pi
    half = math.pi / spokes * 0.45
    pts = [
        (cx + math.cos(a - half) * burst_r_inner, cy + math.sin(a - half) * burst_r_inner),
        (cx + math.cos(a) * burst_r_outer, cy + math.sin(a) * burst_r_outer),
        (cx + math.cos(a + half) * burst_r_inner, cy + math.sin(a + half) * burst_r_inner),
    ]
    bdraw.polygon(pts, fill=(255, 217, 26, 220))
img = Image.alpha_composite(img, burst_layer)

# Layered badge: red ring → yellow ring → white inner → emoji
overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

def disc(r, fill):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)

disc(int(W * 0.135), INK)       # outer black ring (border)
disc(int(W * 0.128), RED)       # red ring
disc(int(W * 0.115), YELLOW)    # yellow ring
disc(int(W * 0.108), INK)       # thin black inner border
disc(int(W * 0.100), WHITE)     # white plate

# Emoji
emoji_size = int(W * 0.155)
font = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', size=160)
emoji_layer = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
edraw = ImageDraw.Draw(emoji_layer)
edraw.text((100, 100), EMOJI, font=font, anchor='mm', embedded_color=True)
emoji_layer = emoji_layer.resize((emoji_size, emoji_size), Image.LANCZOS)
overlay.paste(emoji_layer, (cx - emoji_size // 2, cy - emoji_size // 2), emoji_layer)

img = Image.alpha_composite(img, overlay)

# Decorative star sparkles in the four corners around the badge
sparkle_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(sparkle_layer)
def sparkle(x, y, size, color=YELLOW):
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        r = size if i % 2 == 0 else size * 0.4
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    sdraw.polygon(pts, fill=color)

# Subtle sparkles only (avoid hurting scannability) — placed in the safe central zone
for dx, dy, sz in [(-0.16, -0.08, 18), (0.16, -0.08, 18), (-0.16, 0.08, 18), (0.16, 0.08, 18)]:
    sparkle(cx + W * dx, cy + H * dy, sz, YELLOW)

img = Image.alpha_composite(img, sparkle_layer)

img.save('qr.png', optimize=True)
print(f'wrote qr.png ({W}x{H})')

# =====================================================================
# T-shirt ready: dead simple — QR + bold title beneath, nothing else
# =====================================================================
TITLE_GAP = 60
TITLE_H = 200
SIDE = 80
TOP = 80
BOT = 80
W2 = W + SIDE * 2
H2 = TOP + H + TITLE_GAP + TITLE_H + BOT

tshirt = Image.new('RGBA', (W2, H2), WHITE)
tdraw = ImageDraw.Draw(tshirt)

# Paste the QR centered horizontally
tshirt.paste(img, ((W2 - W) // 2, TOP), img)

# Title beneath
try:
    tf_big = ImageFont.truetype('/System/Library/Fonts/Supplemental/Impact.ttf', size=200)
except Exception:
    tf_big = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', size=200)

title = 'PUNCH POWER!!'
ty = TOP + H + TITLE_GAP + TITLE_H // 2

# render title onto canvas, slight tilt for shonen energy
title_canvas = Image.new('RGBA', (W2, TITLE_H + 80), (0, 0, 0, 0))
tcdraw = ImageDraw.Draw(title_canvas)
cx_t = W2 // 2
cy_t = (TITLE_H + 80) // 2
# red drop shadow
tcdraw.text((cx_t + 10, cy_t + 10), title, font=tf_big, fill=RED, anchor='mm')
# black thick outline
for dx in range(-5, 6, 2):
    for dy in range(-5, 6, 2):
        if dx == 0 and dy == 0:
            continue
        tcdraw.text((cx_t + dx, cy_t + dy), title, font=tf_big, fill=INK, anchor='mm')
tcdraw.text((cx_t, cy_t), title, font=tf_big, fill=WHITE, anchor='mm')
title_canvas = title_canvas.rotate(-3, resample=Image.BICUBIC)
tshirt.paste(title_canvas, (0, ty - title_canvas.size[1] // 2), title_canvas)

tshirt.save('qr_tshirt.png', optimize=True)
print(f'wrote qr_tshirt.png ({W2}x{H2})')

# Cleanup older outputs that we no longer use
import os
for old in ('qr_framed.png', 'qr_tshirt_dark.png'):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), old)
    if os.path.exists(p):
        os.remove(p)
