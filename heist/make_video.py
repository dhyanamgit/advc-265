import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

W, H = 960, 540
FPS = 24
OUT = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(OUT, "frames")
os.makedirs(FRAMES, exist_ok=True)

SKY = (135, 206, 250)
SUN = (255, 220, 60)
BUILDING = (222, 184, 135)
ROOF = (178, 130, 90)
SIGN_BG = (70, 130, 180)
DOOR = (120, 72, 32)
GLASS = (180, 220, 240)
WALL = (245, 240, 220)
FLOOR = (205, 205, 205)
COUNTER = (139, 90, 43)
COUNTER_TOP = (170, 115, 65)
SKIN = (241, 194, 125)
ROBBER_BODY = (45, 45, 70)
MASK = (20, 20, 20)
GUN = (70, 70, 70)
BAG = (170, 115, 50)
CASHIER_BODY = (0, 150, 150)
HAIR = (90, 50, 20)
PINK = (255, 105, 180)
BROCCOLI = (60, 160, 60)
ALLEY = (120, 120, 128)
BRICK = (105, 105, 112)
CAR = (40, 80, 180)


def font(size):
    return ImageFont.load_default(size=size)


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def seg(t, a, b):
    if b <= a:
        return 1.0
    return clamp((t - a) / (b - a))


def outlined(d, xy, s, f, fill=(255, 255, 255), outline=(0, 0, 0), w=2, anchor="mm"):
    x, y = xy
    for dx in (-w, 0, w):
        for dy in (-w, 0, w):
            if dx or dy:
                d.text((x + dx, y + dy), s, font=f, fill=outline, anchor=anchor)
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)


def wrap_text(d, text, f, max_w):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def caption(d, s, fsize=26):
    bar_h = 54
    d.rectangle([0, H - bar_h, W, H], fill=(18, 18, 26))
    d.line([0, H - bar_h, W, H - bar_h], fill=(255, 210, 63), width=3)
    outlined(d, (W // 2, H - bar_h // 2), s, font(fsize), fill=(255, 255, 255), w=2)


def bubble(d, xy, text, tail, fsize=24, max_w=360):
    f = font(fsize)
    lines = wrap_text(d, text, f, max_w)
    pad = 14
    line_h = fsize + 8
    tw = max(d.textlength(line, font=f) for line in lines)
    bw = tw + pad * 2
    bh = line_h * len(lines) + pad * 2
    x, y = xy
    d.rounded_rectangle([x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2], radius=14,
                        fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    tx, ty = tail
    d.polygon([(x - 12, y + bh / 2 - 6), (x + 12, y + bh / 2 - 6), (tx, ty)],
              fill=(255, 255, 255), outline=(0, 0, 0))
    d.rectangle([x - 12, y + bh / 2 - 10, x + 12, y + bh / 2 - 2], fill=(255, 255, 255))
    for i, line in enumerate(lines):
        d.text((x, y - bh / 2 + pad + line_h * i + line_h / 2), line, font=f,
               fill=(20, 20, 20), anchor="mm")


def draw_robber(d, x, y, s=1.0, gun=True, bag=False, pink=False, surprised=False, arms_up=False):
    bob = abs(math.sin(x * 0.05)) * 4 if gun else 0
    y = y - bob
    d.rectangle([x - 13 * s, y - 40 * s, x - 3 * s, y], fill=(30, 30, 45))
    d.rectangle([x + 3 * s, y - 40 * s, x + 13 * s, y], fill=(30, 30, 45))
    d.rounded_rectangle([x - 21 * s, y - 82 * s, x + 21 * s, y - 36 * s], radius=10, fill=ROBBER_BODY)
    hy = y - 100 * s
    head_fill = PINK if pink else SKIN
    d.ellipse([x - 20 * s, hy - 20 * s, x + 20 * s, hy + 20 * s], fill=head_fill, outline=(0, 0, 0), width=2)
    d.rectangle([x - 20 * s, hy - 8 * s, x + 20 * s, hy + 6 * s], fill=MASK)
    if surprised:
        d.ellipse([x - 11 * s, hy - 5 * s, x - 3 * s, hy + 3 * s], fill=(255, 255, 255), outline=(0, 0, 0))
        d.ellipse([x + 3 * s, hy - 5 * s, x + 11 * s, hy + 3 * s], fill=(255, 255, 255), outline=(0, 0, 0))
        d.ellipse([x - 4 * s, hy + 10 * s, x + 4 * s, hy + 17 * s], fill=(120, 40, 40))
    else:
        d.ellipse([x - 10 * s, hy - 4 * s, x - 3 * s, hy + 3 * s], fill=(255, 255, 255))
        d.ellipse([x + 3 * s, hy - 4 * s, x + 10 * s, hy + 3 * s], fill=(255, 255, 255))
    if arms_up:
        d.line([x - 18 * s, y - 76 * s, x - 34 * s, y - 104 * s], fill=ROBBER_BODY, width=max(1, int(9 * s)))
        d.line([x + 18 * s, y - 76 * s, x + 34 * s, y - 104 * s], fill=ROBBER_BODY, width=max(1, int(9 * s)))
        if gun:
            d.polygon([(x - 38 * s, y - 108 * s), (x - 26 * s, y - 112 * s), (x - 26 * s, y - 100 * s), (x - 38 * s, y - 96 * s)], fill=GUN)
    else:
        d.line([x + 16 * s, y - 70 * s, x + 34 * s, y - 62 * s], fill=ROBBER_BODY, width=max(1, int(9 * s)))
        if gun:
            d.polygon([(x + 32 * s, y - 70 * s), (x + 58 * s, y - 64 * s), (x + 58 * s, y - 56 * s), (x + 32 * s, y - 56 * s)], fill=GUN)
        if bag:
            bx, by = x - 34 * s, y - 52 * s
            d.ellipse([bx - 16 * s, by - 14 * s, bx + 16 * s, by + 18 * s], fill=BAG, outline=(0, 0, 0), width=2)
            d.text((bx, by + 2 * s), "$", font=font(int(26 * s)), fill=(255, 255, 230), anchor="mm")
            d.line([x - 16 * s, y - 70 * s, bx, by], fill=ROBBER_BODY, width=max(1, int(9 * s)))


def draw_cashier(d, x, y, s=1.0, wink=False, thumbs_up=False, mouth="smile"):
    d.rectangle([x - 13 * s, y - 40 * s, x - 3 * s, y], fill=(0, 110, 110))
    d.rectangle([x + 3 * s, y - 40 * s, x + 13 * s, y], fill=(0, 110, 110))
    d.rounded_rectangle([x - 21 * s, y - 82 * s, x + 21 * s, y - 36 * s], radius=10, fill=CASHIER_BODY)
    hy = y - 100 * s
    d.ellipse([x - 20 * s, hy - 20 * s, x + 20 * s, hy + 20 * s], fill=SKIN, outline=(0, 0, 0), width=2)
    d.arc([x - 21 * s, hy - 30 * s, x + 21 * s, hy + 6 * s], start=180, end=360, fill=HAIR, width=10)
    if wink:
        d.ellipse([x - 11 * s, hy - 5 * s, x - 3 * s, hy + 3 * s], fill=(255, 255, 255), outline=(0, 0, 0))
        d.line([x + 3 * s, hy - 1 * s, x + 11 * s, hy - 1 * s], fill=(0, 0, 0), width=2)
    else:
        d.ellipse([x - 11 * s, hy - 5 * s, x - 3 * s, hy + 3 * s], fill=(255, 255, 255), outline=(0, 0, 0))
        d.ellipse([x + 3 * s, hy - 5 * s, x + 11 * s, hy + 3 * s], fill=(255, 255, 255), outline=(0, 0, 0))
    if mouth == "smile":
        d.arc([x - 8 * s, hy + 4 * s, x + 8 * s, hy + 14 * s], start=0, end=180, fill=(120, 40, 40), width=2)
    elif mouth == "o":
        d.ellipse([x - 4 * s, hy + 8 * s, x + 4 * s, hy + 16 * s], fill=(120, 40, 40))
    if thumbs_up:
        d.line([x + 18 * s, y - 70 * s, x + 34 * s, y - 88 * s], fill=CASHIER_BODY, width=max(1, int(9 * s)))
        d.ellipse([x + 30 * s, y - 98 * s, x + 40 * s, y - 86 * s], fill=SKIN, outline=(0, 0, 0), width=2)


def draw_guard_mannequin(d, x, y):
    d.rounded_rectangle([x - 18, y - 80, x + 18, y - 30], radius=8, fill=(190, 190, 195), outline=(0, 0, 0), width=2)
    d.ellipse([x - 16, y - 108, x + 16, y - 76], fill=(210, 210, 215), outline=(0, 0, 0), width=2)
    d.line([x - 16, y - 30, x - 10, y], fill=(160, 160, 165), width=8)
    d.line([x + 10, y - 30, x + 16, y], fill=(160, 160, 165), width=8)
    d.text((x + 34, y - 120), "Z", font=font(28), fill=(90, 90, 160))
    d.text((x + 52, y - 140), "z", font=font(22), fill=(110, 110, 180))
    d.text((x + 66, y - 156), "z", font=font(16), fill=(130, 130, 200))


def bank_exterior(d, robber_x=None, dye=False):
    d.rectangle([0, 0, W, H], fill=SKY)
    d.ellipse([780, 40, 860, 120], fill=SUN)
    d.rectangle([0, 460, W, H], fill=(150, 150, 150))
    d.rectangle([240, 130, 720, 470], fill=BUILDING, outline=(120, 90, 60), width=4)
    d.rectangle([220, 100, 740, 140], fill=ROOF)
    d.rounded_rectangle([330, 60, 630, 105], radius=8, fill=SIGN_BG, outline=(255, 255, 255), width=3)
    outlined(d, (480, 82), "GRAND BANK", font(38), fill=(255, 255, 255))
    for wx in (280, 640):
        d.rectangle([wx, 170, wx + 60, 240], fill=GLASS, outline=(120, 90, 60), width=3)
    d.rectangle([440, 330, 520, 470], fill=DOOR, outline=(80, 50, 20), width=3)
    d.ellipse([505, 395, 517, 407], fill=(255, 210, 63))
    if robber_x is not None:
        draw_robber(d, robber_x, 470, bag=True, pink=dye)


def bank_interior(d):
    d.rectangle([0, 0, W, H], fill=WALL)
    d.rectangle([0, 400, W, H], fill=FLOOR)
    for gx in range(0, W, 80):
        d.line([gx, 400, gx - 40, H], fill=(180, 180, 180), width=2)
    d.rounded_rectangle([330, 40, 630, 95], radius=8, fill=SIGN_BG, outline=(200, 200, 200), width=3)
    outlined(d, (480, 68), "GRAND BANK", font(36), fill=(255, 255, 255))
    d.rectangle([120, 380, 840, 470], fill=COUNTER, outline=(90, 55, 25), width=4)
    d.rectangle([110, 366, 850, 392], fill=COUNTER_TOP, outline=(90, 55, 25), width=3)
    d.rounded_rectangle([140, 180, 260, 300], radius=6, fill=GLASS, outline=(120, 90, 60), width=3)
    outlined(d, (200, 240), "ATM", font(30), fill=(60, 60, 60))
    draw_guard_mannequin(d, 880, 460)


def draw_bag(d, x, y, s=1.0, open_=False, broccoli=False):
    d.ellipse([x - 22 * s, y - 16 * s, x + 22 * s, y + 22 * s], fill=BAG, outline=(0, 0, 0), width=2)
    if open_:
        d.polygon([(x - 18 * s, y - 12 * s), (x + 18 * s, y - 12 * s), (x, y - 34 * s)], fill=(120, 80, 35), outline=(0, 0, 0))
        if broccoli:
            for i, (bx, by, r) in enumerate([(-10, -18, 10), (4, -24, 11), (14, -14, 9), (-2, -12, 9)]):
                d.ellipse([x + bx * s - r * s, y + by * s - r * s, x + bx * s + r * s, y + by * s + r * s], fill=BROCCOLI, outline=(20, 90, 20), width=2)
    else:
        d.text((x, y + 4 * s), "$", font=font(int(28 * s)), fill=(255, 255, 230), anchor="mm")


def scene_title(d, t, dur):
    d.rectangle([0, 0, W, H], fill=(10, 10, 18))
    p = ease(seg(t, 0.2, 1.0))
    size = int(lerp(20, 72, p))
    outlined(d, (W // 2, H // 2 - 30), "THE PERFECT HEIST", font(size), fill=(255, 210, 63), w=3)
    if seg(t, 1.4, 2.2) > 0:
        a = ease(seg(t, 1.4, 2.2))
        outlined(d, (W // 2, H // 2 + 50), "(a 100% true story)", font(int(lerp(10, 28, a))), fill=(255, 255, 255), w=2)
    d.text((W // 2, H - 40), "an animated original", font=font(18), fill=(150, 150, 160), anchor="mm")


def scene_exterior(d, t, dur):
    x = lerp(1020, 480, ease(seg(t, 0.4, 2.6)))
    bank_exterior(d, robber_x=x if x < 1000 else None)
    caption(d, "Tuesday, 10:02 AM. A perfectly normal day at the bank.")


def scene_confront(d, t, dur):
    bank_interior(d)
    rx = lerp(-60, 310, ease(seg(t, 0.2, 1.4)))
    draw_cashier(d, 640, 420)
    draw_robber(d, rx, 470, gun=True)
    if seg(t, 1.6, 2.2) > 0:
        bubble(d, (300, 150), "GIVE ME ALL THE MONEY! THIS IS A ROBBERY!", (rx + 10, 360), fsize=24)
    if seg(t, 3.0, 3.6) > 0:
        bubble(d, (640, 200), "Of course! One moment :)", (640, 330), fsize=24)
    caption(d, "The 'robbery' begins. The guard is... asleep?")


def scene_switch(d, t, dur):
    bank_interior(d)
    draw_cashier(d, 640, 420, wink=seg(t, 3.2, 3.8) > 0.5)
    draw_robber(d, 310, 470, gun=False, bag=seg(t, 2.0, 99) > 0)
    bag_x = lerp(600, 340, ease(seg(t, 0.9, 1.7)))
    if seg(t, 0.9, 1.9) > 0:
        draw_bag(d, bag_x, 372)
    if seg(t, 2.6, 3.0) > 0:
        d.ellipse([150, 430, 186, 466], fill=(220, 40, 40), outline=(0, 0, 0), width=3)
        outlined(d, (168, 448), "!", font(26), fill=(255, 255, 255))
        outlined(d, (240, 448), "BEEP", font(22), fill=(255, 80, 80))
    caption(d, "TWIST #1: she hit the silent alarm. (The guard was a mannequin.)")


def scene_dye(d, t, dur):
    boom = seg(t, 2.8, 3.2)
    if t < 3.6:
        x = lerp(500, 940, seg(t, 0.3, 2.8))
        bank_exterior(d, robber_x=x, dye=boom > 0.3)
        bx, by = x, 430
    else:
        x = lerp(940, 1060, ease(seg(t, 3.6, 5.6)))
        bank_exterior(d, robber_x=x if x < 1040 else None, dye=True)
        bx, by = 940, 430
    if boom > 0:
        r = 30 + 90 * ease(boom)
        for i in range(10):
            ang = i * 0.628
            cx = bx + math.cos(ang) * r * 1.3
            cy = by + math.sin(ang) * r * 0.8
            d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=PINK, outline=(200, 60, 140), width=2)
        outlined(d, (bx, by - 90), "POOF!", font(44), fill=PINK, outline=(120, 20, 70), w=3)
    caption(d, "TWIST #2: dye pack! The getaway is ruined.")


def scene_alley(d, t, dur):
    d.rectangle([0, 0, W, H], fill=ALLEY)
    for by in range(0, H, 60):
        d.line([0, by, W, by], fill=BRICK, width=3)
        off = 40 if (by // 60) % 2 else 0
        for bx in range(off, W, 90):
            d.line([bx, by, bx, min(by + 60, H)], fill=BRICK, width=3)
    d.rectangle([0, 470, W, H], fill=(90, 90, 95))
    opened = seg(t, 1.2, 1.8)
    draw_robber(d, 300, 480, gun=False, bag=False, pink=True, surprised=opened > 0.5)
    draw_bag(d, 380, 400, s=1.4, open_=opened > 0.5, broccoli=opened > 0.5)
    if seg(t, 2.2, 2.8) > 0:
        bubble(d, (300, 170), "Wait... this is BROCCOLI?!", (300, 330), fsize=24)
    car_x = lerp(1100, 620, ease(seg(t, 3.4, 4.4)))
    if car_x < 1080:
        d.rounded_rectangle([car_x, 380, car_x + 260, 460], radius=14, fill=CAR, outline=(0, 0, 0), width=3)
        d.rounded_rectangle([car_x + 50, 340, car_x + 190, 388], radius=10, fill=CAR, outline=(0, 0, 0), width=3)
        d.rectangle([car_x + 70, 352, car_x + 120, 372], fill=GLASS)
        d.rectangle([car_x + 130, 352, car_x + 170, 372], fill=GLASS)
        d.ellipse([car_x + 40, 452, car_x + 80, 492], fill=(20, 20, 20))
        d.ellipse([car_x + 200, 452, car_x + 240, 492], fill=(20, 20, 20))
        if int(t * 6) % 2 == 0:
            d.ellipse([car_x + 118, 330, car_x + 142, 352], fill=(255, 60, 60))
        else:
            d.ellipse([car_x + 118, 330, car_x + 142, 352], fill=(80, 140, 255))
    if seg(t, 5.2, 5.8) > 0:
        draw_robber(d, 300, 480, gun=False, bag=False, pink=True, arms_up=True)
        bubble(d, (620, 180), "I SURRENDER!", (330, 350), fsize=24)
    if seg(t, 4.6, 99) > 0:
        caption(d, "TWIST #4: police arrive — thanks to the 'silent' alarm.")
    elif seg(t, 2.2, 99) > 0:
        caption(d, "TWIST #3: the cash was swapped... for broccoli.")


def scene_end(d, t, dur):
    d.rectangle([0, 0, W, H], fill=(10, 10, 18))
    if seg(t, 0.3, 1.0) > 0:
        outlined(d, (W // 2, 110), "TWIST #5:", font(40), fill=(255, 210, 63), w=3)
    if seg(t, 1.2, 2.0) > 0:
        outlined(d, (W // 2, 190), "IT WAS A DRILL ALL ALONG.", font(44), fill=(255, 255, 255), w=3)
    if seg(t, 2.4, 3.2) > 0:
        d.rounded_rectangle([W // 2 - 260, 240, W // 2 + 260, 310], radius=10, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
        d.rectangle([W // 2 - 250, 252, W // 2 - 210, 298], fill=(200, 60, 60))
        outlined(d, (W // 2 + 20, 275), "NAME TAG:  'BRAD — SUMMER INTERN'", font(26), fill=(20, 20, 20), outline=(255, 255, 255), w=1)
    if seg(t, 3.6, 4.4) > 0:
        draw_cashier(d, W // 2 - 160, 470, s=1.1, thumbs_up=True)
        draw_robber(d, W // 2 + 160, 480, gun=False, pink=True, arms_up=True)
    if seg(t, 5.0, 5.8) > 0:
        outlined(d, (W // 2, 440), "THE END", font(52), fill=(255, 210, 63), w=3)


SCENES = [
    (3.0, scene_title),
    (6.0, scene_exterior),
    (7.0, scene_confront),
    (7.0, scene_switch),
    (7.0, scene_dye),
    (7.0, scene_alley),
    (7.0, scene_end),
]


def render_frame(i):
    t_global = i / FPS
    acc = 0.0
    for dur, fn in SCENES:
        if t_global < acc + dur:
            img = Image.new("RGB", (W, H), (0, 0, 0))
            d = ImageDraw.Draw(img)
            fn(d, t_global - acc, dur)
            img.save(os.path.join(FRAMES, f"frame_{i:04d}.png"))
            return
        acc += dur
    raise RuntimeError("time overflow")


def main():
    total = int(sum(d for d, _ in SCENES) * FPS)
    print(f"rendering {total} frames at {FPS} fps ({W}x{H})")
    for i in range(total):
        render_frame(i)
        if i % 120 == 0:
            print(f"  {i}/{total}")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    mp4 = os.path.join(OUT, "heist.mp4")
    gif = os.path.join(OUT, "heist_preview.gif")
    base = [ff, "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "frame_%04d.png")]
    r = subprocess.run(base + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                               "-movflags", "+faststart", mp4], capture_output=True, text=True)
    if r.returncode != 0:
        print("libx264 failed, falling back to mpeg4:", r.stderr[-300:])
        r = subprocess.run(base + ["-c:v", "mpeg4", "-q:v", "3", mp4], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-500:])
            raise SystemExit(1)
    vf = "fps=12,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
    r = subprocess.run(base + ["-vf", vf, gif], capture_output=True, text=True)
    if r.returncode != 0:
        print("gif failed:", r.stderr[-300:])
    for p in (mp4, gif):
        if os.path.exists(p):
            print(p, os.path.getsize(p) / 1e6, "MB")


if __name__ == "__main__":
    main()
