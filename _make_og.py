"""
Generate OGP images per level + landing pages with level-specific OGP meta.

Outputs:
  og/main.png                   - default OGP for the site
  og/lv-0.png ... og/lv-19.png  - per-level OGP images
  c/0/index.html ... c/19/index.html
                                - landing pages with level-specific OGP meta
                                  + JS redirect to ../../?<params>

Static OG scrapers (Twitter/Slack/etc.) read meta from c/{level}/index.html;
real users hit JS redirect and land on the main app with battle params.
"""
import os
import shutil
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://ta1m1kam.github.io/punchpunchpunch'

LEVELS = [
    ('人間', '赤ちゃん',             'お前ほんとにパンチした？'),
    ('人間', '子供',                 'お年玉でジュース買えそう。'),
    ('人間', '一般市民',             '平和主義だな、安心した。'),
    ('人間', '事務職',               'デスクワーク向きの拳。'),
    ('人間', '体育会系',             '部活やってた？って感じ。'),
    ('人間', 'ケンカ自慢',           '街でちょっと有名なタイプ。'),
    ('人間', 'ヤンキー',             '夜の公園の主か？'),
    ('人間', 'アマチュアボクサー',   '練習してるな？やるじゃん。'),
    ('人間', 'プロ格闘家',           'お前、格闘家？'),
    ('人間', '世界ランカー',         'お前、世界ランカーか？'),
    ('超人', '覚醒人類',             '人間の壁、突破。'),
    ('超人', '異能者',               'お前、何か覚醒したな？'),
    ('超人', 'ヒーロー',             'マントいる？'),
    ('超人', '怪人',                 'ヒーロー協会から討伐依頼が来てる。'),
    ('超人', '改造人間',             '腕に何か仕込んだろ。'),
    ('超人', '半神',                 '神域に片足突っ込んでる。'),
    ('超人', '雷神',                 'スマホから雷鳴った。'),
    ('超人', '破壊神',               '次元を割らないでくれ。'),
    ('超人', '創造主',               '世界を創るタイプの拳。'),
    ('超人', '全知全能',             '神も恐れる存在。お前、誰だ？'),
]

RED = (255, 43, 59)
YELLOW = (255, 217, 26)
INK = (10, 10, 15)
WHITE = (255, 255, 255)

JP_FONT = '/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc'
IMPACT = '/System/Library/Fonts/Supplemental/Impact.ttf'
EMOJI = '/System/Library/Fonts/Apple Color Emoji.ttc'


def fit_font(path, text, max_width, max_size, min_size=40, step=4):
    for s in range(max_size, min_size, -step):
        f = ImageFont.truetype(path, size=s)
        if f.getlength(text) <= max_width:
            return f, s
    return ImageFont.truetype(path, size=min_size), min_size


def draw_text_with_outline(draw, xy, text, font, fill, outline=INK, shadow=None,
                           outline_width=4, anchor='mm'):
    x, y = xy
    if shadow is not None:
        sc, dx, dy = shadow
        draw.text((x + dx, y + dy), text, font=font, fill=sc, anchor=anchor)
    if outline_width > 0:
        for ox in range(-outline_width, outline_width + 1, max(1, outline_width // 2)):
            for oy in range(-outline_width, outline_width + 1, max(1, outline_width // 2)):
                if ox == 0 and oy == 0:
                    continue
                draw.text((x + ox, y + oy), text, font=font, fill=outline, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def halftone(size, color=(255, 255, 255, 14), step=10, dot=1):
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, size[1], step):
        for x in range(((y // step) % 2) * (step // 2), size[0], step):
            d.ellipse((x - dot, y - dot, x + dot, y + dot), fill=color)
    return layer


def radial_burst(size, center, color=YELLOW, alpha=80, spokes=20, r_inner_ratio=0.05, r_outer_ratio=0.55):
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    R = max(size) * r_outer_ratio
    Ri = max(size) * r_inner_ratio
    half = math.pi / spokes * 0.42
    for i in range(spokes):
        a = (i / spokes) * 2 * math.pi
        pts = [
            (cx + math.cos(a - half) * Ri, cy + math.sin(a - half) * Ri),
            (cx + math.cos(a) * R, cy + math.sin(a) * R),
            (cx + math.cos(a + half) * Ri, cy + math.sin(a + half) * Ri),
        ]
        d.polygon(pts, fill=color + (alpha,))
    return layer


def emoji_image(char, size_px):
    # Apple Color Emoji.ttc has fixed bitmap; render at 160 then resize.
    f = ImageFont.truetype(EMOJI, size=160)
    canvas = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((100, 100), char, font=f, anchor='mm', embedded_color=True)
    return canvas.resize((size_px, size_px), Image.LANCZOS)


def make_level_og(level, tier, archetype, verdict, score_lo, score_hi):
    W, H = 1200, 630
    is_super = (tier == '超人')

    # Background — dark with red radial bias
    img = Image.new('RGB', (W, H), INK)
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    # Radial gradient using concentric ellipses
    cx, cy = W // 2, int(H * 0.45)
    for r in range(int(max(W, H) * 0.7), 0, -8):
        alpha = max(0, int(48 - r * 0.04))
        col = RED if not is_super else (180, 20, 30)
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (alpha,))
    img = Image.alpha_composite(img.convert('RGBA'), grad)

    # Halftone overlay
    img = Image.alpha_composite(img, halftone((W, H), color=(255, 255, 255, 16), step=10, dot=1))

    # Radial burst behind archetype
    burst = radial_burst((W, H), (cx, cy + 30),
                         color=YELLOW if is_super else (255, 200, 60),
                         alpha=70 if is_super else 50,
                         spokes=22, r_inner_ratio=0.04, r_outer_ratio=0.62)
    img = Image.alpha_composite(img, burst)

    draw = ImageDraw.Draw(img)

    # Brand bar top-left
    brand_font = ImageFont.truetype(IMPACT, size=42)
    draw_text_with_outline(draw, (60 + 8, 56), 'PUNCH PUNCH PUNCH',
                           font=brand_font, fill=WHITE, outline=INK,
                           shadow=(RED, 4, 4), outline_width=3, anchor='lm')

    # Tier badge top-right
    tier_text = f'{tier} 階級'
    tier_font = ImageFont.truetype(JP_FONT, size=30)
    tier_w = tier_font.getlength(tier_text)
    pad_x, pad_y = 18, 10
    bx2, by1 = W - 60, 30
    bx1 = bx2 - int(tier_w) - pad_x * 2
    by2 = by1 + 30 + pad_y * 2
    badge_bg = RED if is_super else WHITE
    badge_fg = YELLOW if is_super else INK
    draw.rectangle((bx1, by1, bx2, by2), fill=badge_bg, outline=INK, width=4)
    draw.text(((bx1 + bx2) // 2, (by1 + by2) // 2), tier_text,
              font=tier_font, fill=badge_fg, anchor='mm')

    # Hero archetype name (BIG)
    name_font, _ = fit_font(JP_FONT, archetype, max_width=W - 140, max_size=200, min_size=80)
    name_y = int(H * 0.46)
    draw_text_with_outline(draw, (W // 2, name_y), archetype,
                           font=name_font, fill=YELLOW, outline=INK,
                           shadow=(RED, 10, 10), outline_width=5, anchor='mm')

    # Score / Lv pill below archetype
    score_text = f'Lv.{level}  /  {score_lo}–{score_hi} PWR'
    sc_font = ImageFont.truetype(IMPACT, size=44)
    sc_w = sc_font.getlength(score_text)
    pad = 24
    pill_y = name_y + int(name_font.size * 0.62) + 36
    pill_x1 = W // 2 - int(sc_w) // 2 - pad
    pill_x2 = W // 2 + int(sc_w) // 2 + pad
    pill_y1 = pill_y - 36
    pill_y2 = pill_y + 36
    draw.rectangle((pill_x1, pill_y1, pill_x2, pill_y2),
                   fill=INK, outline=YELLOW, width=4)
    draw.text((W // 2, pill_y), score_text, font=sc_font, fill=YELLOW, anchor='mm')

    # Verdict at bottom
    v_font, _ = fit_font(JP_FONT, verdict, max_width=W - 140, max_size=44, min_size=28)
    draw.text((W // 2, H - 60), verdict, font=v_font, fill=WHITE, anchor='mm')

    # 🥊 emoji top-left accent
    glove = emoji_image('🥊', 110)
    img.paste(glove, (40, H - 150), glove)

    img.convert('RGB').save(os.path.join(ROOT, 'og', f'lv-{level}.png'),
                            optimize=True, quality=88)


def make_main_og():
    W, H = 1200, 630
    img = Image.new('RGB', (W, H), INK)
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    cx, cy = W // 2, int(H * 0.42)
    for r in range(int(max(W, H) * 0.7), 0, -8):
        alpha = max(0, int(56 - r * 0.04))
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED + (alpha,))
    img = Image.alpha_composite(img.convert('RGBA'), grad)
    img = Image.alpha_composite(img, halftone((W, H), color=(255, 255, 255, 14), step=10, dot=1))
    img = Image.alpha_composite(img, radial_burst((W, H), (cx, cy + 20), color=YELLOW, alpha=60))

    draw = ImageDraw.Draw(img)

    # Hero: PUNCH × 3 (stacked, alternating color, slight offsets for shonen energy)
    hero_font = ImageFont.truetype(IMPACT, size=190)
    rows = [
        ('PUNCH',   WHITE,  -12, 110),
        ('PUNCH',   YELLOW, +18, 290),
        ('PUNCH!!', WHITE,  -8,  470),
    ]
    for text, fill, dx, y in rows:
        draw_text_with_outline(
            draw, (W // 2 + dx, y), text,
            font=hero_font, fill=fill,
            outline=INK, shadow=(RED, 12, 12),
            outline_width=6, anchor='mm',
        )

    # Subtitle
    sf2 = ImageFont.truetype(IMPACT, size=36)
    draw.text((W // 2, H - 28), '0–200 PWR / SCAN & PUNCH ME!!',
              font=sf2, fill=YELLOW, anchor='mm')

    # 🥊 emoji corners
    g1 = emoji_image('🥊', 130)
    img.paste(g1, (50, 40), g1)
    img.paste(g1.transpose(Image.FLIP_LEFT_RIGHT), (W - 50 - 130, 40), g1.transpose(Image.FLIP_LEFT_RIGHT))

    img.convert('RGB').save(os.path.join(ROOT, 'og', 'main.png'),
                            optimize=True, quality=88)


def make_landing_pages():
    """Tiny HTML pages at /c/{lv}/index.html with level-specific OGP meta + JS redirect."""
    template = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PUNCH PUNCH PUNCH / Lv.{lv} {archetype}</title>
<meta name="description" content="{verdict} お前のパンチ力は何点だ？" />
<meta property="og:type" content="website" />
<meta property="og:title" content="VS {archetype} (Lv.{lv}) / PUNCH PUNCH PUNCH" />
<meta property="og:description" content="{verdict} お前も殴って倒せ！" />
<meta property="og:image" content="{site}/og/lv-{lv}.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:url" content="{site}/c/{lv}/" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="VS {archetype} (Lv.{lv}) / PUNCH PUNCH PUNCH" />
<meta name="twitter:description" content="{verdict}" />
<meta name="twitter:image" content="{site}/og/lv-{lv}.png" />
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='86'>🥊</text></svg>" />
<style>
  html,body{{margin:0;padding:0;height:100%;background:#0a0a0f;color:#f5f5f5;font-family:system-ui,-apple-system,sans-serif;display:grid;place-items:center}}
  a{{color:#ffd91a;text-decoration:none;border-bottom:2px solid #ffd91a;padding:8px 14px}}
  p{{opacity:.7;margin:8px 0}}
</style>
</head>
<body>
<div style="text-align:center">
  <p style="font-size:14px;letter-spacing:.3em">REDIRECTING…</p>
  <p style="font-size:24px"><b>VS {archetype}</b> (Lv.{lv})</p>
  <p><a href="../../">アプリを開く</a></p>
</div>
<script>
(function(){{
  var p = location.search || '';
  if (!/(^|[?&])c=/.test(p)) {{
    p = (p ? p + '&' : '?') + 'c={mid}';
  }}
  location.replace('../../' + p);
}})();
</script>
</body>
</html>
'''
    for lv, (tier, archetype, verdict) in enumerate(LEVELS):
        d = os.path.join(ROOT, 'c', str(lv))
        os.makedirs(d, exist_ok=True)
        score_lo = lv * 10
        score_hi = lv * 10 + 9 if lv < len(LEVELS) - 1 else 200
        mid = lv * 10 + (5 if lv < len(LEVELS) - 1 else 5)
        html = template.format(
            lv=lv,
            archetype=archetype,
            verdict=verdict,
            site=SITE,
            mid=mid,
        )
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)


# ---- Run ----
shutil.rmtree(os.path.join(ROOT, 'og'), ignore_errors=True)
shutil.rmtree(os.path.join(ROOT, 'c'), ignore_errors=True)
os.makedirs(os.path.join(ROOT, 'og'), exist_ok=True)

make_main_og()
print('wrote og/main.png')
for lv, (tier, archetype, verdict) in enumerate(LEVELS):
    score_lo = lv * 10
    score_hi = lv * 10 + 9 if lv < len(LEVELS) - 1 else 200
    make_level_og(lv, tier, archetype, verdict, score_lo, score_hi)
print(f'wrote og/lv-0.png .. og/lv-{len(LEVELS)-1}.png')

make_landing_pages()
print(f'wrote c/0/index.html .. c/{len(LEVELS)-1}/index.html')
