#!/usr/bin/env python3
"""Professional interior walkthrough video builder.
Usage: build_walkthrough.py <out.mp4> <W> <H>
Produces: intro card -> per-room eased Ken Burns clips with cinematic grade,
vignette, film grain and elegant room-name lower-thirds -> outro card,
stitched with varied transitions over a layered ambient music bed + whoosh SFX.
"""
import os, sys, glob, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = sys.argv[1] if len(sys.argv) > 1 else "walkthrough_16x9.mp4"
W   = int(sys.argv[2]) if len(sys.argv) > 2 else 1920
H   = int(sys.argv[3]) if len(sys.argv) > 3 else 1080
FPS = 30
DUR = 3.2          # per room
CARD = 3.0         # intro/outro
T   = 0.7          # transition

FONTS = "/mnt/skills/examples/canvas-design/canvas-fonts"
F_DISP = os.path.join(FONTS, "Italiana-Regular.ttf")      # elegant display
F_THX  = os.path.join(FONTS, "Gloock-Regular.ttf")        # high-contrast serif
F_SANS = os.path.join(FONTS, "InstrumentSans-Regular.ttf")

CREAM = (239, 233, 221); GOLD = (201, 168, 106); DIM = (170, 162, 148)

# ---- room order + display names -------------------------------------------
NAMES = {
    "entrance area": "Entrance Foyer",
    "wall pannaling and livingarea": "Living Area",
    "Hall": "Living Hall",
    "ROOM": "Living Room",
    "studytablenadtvunit": "Study & TV Unit",
    "L-kitechen": "Modular Kitchen",
    "diningare": "Dining Area",
    "dinner area": "Dining Space",
    "3rd view dinner area": "Dining View",
    "2ndbedroom": "Second Bedroom",
    "bed-frount": "Master Bedroom",
    "bedroom-wardrobe": "Bedroom Wardrobe",
    "2nd wardrobe": "Wardrobe Unit",
    "2nd study table": "Study Corner",
}
PREFERRED = list(NAMES.keys())
imgs = glob.glob("*.jp*g") + glob.glob("*.png") + glob.glob("*.webp")
def rank(f):
    b = os.path.splitext(os.path.basename(f))[0]
    return PREFERRED.index(b) if b in PREFERRED else len(PREFERRED)
imgs = sorted(imgs, key=lambda f: (rank(f), f.lower()))
if not imgs: sys.exit("No images found")

tmp = tempfile.mkdtemp(prefix="wt_")
frames = int(DUR * FPS); Fden = frames - 1
def run(cmd):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *cmd])
    if r.returncode: sys.exit("ffmpeg failed near: " + " ".join(map(str, cmd[:8])))

def font(p, s): return ImageFont.truetype(p, s)
def tracked(draw, xy, text, fnt, fill, tr=0, anchor="la"):
    """Draw text with letter-spacing. anchor 'la'(left) or 'ma'(center)."""
    widths = [draw.textlength(c, font=fnt) for c in text]
    total = sum(widths) + tr * (len(text) - 1)
    x, y = xy
    if anchor == "ma": x -= total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill)
        x += w + tr

# ---- intro / outro cards ---------------------------------------------------
def gradient_bg(w, h, top=(22, 21, 18), bot=(11, 10, 9)):
    bg = Image.new("RGB", (w, h))
    px = bg.load()
    for y in range(h):
        t = y / h
        px_row = tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3))
        for x in range(w): px[x, y] = px_row
    return bg

def card(path, kicker, title_lines, sub, big_font=F_DISP):
    im = gradient_bg(W, H); d = ImageDraw.Draw(im)
    cx = W // 2
    S = H / 1080.0
    # kicker (small caps, gold, tracked)
    fk = font(F_SANS, int(30*S))
    tracked(d, (cx, int(H*0.30)), kicker.upper(), fk, GOLD, tr=int(10*S), anchor="ma")
    # title
    ft = font(big_font, int(132*S))
    y = int(H*0.36)
    for ln in title_lines:
        tracked(d, (cx, y), ln, ft, CREAM, tr=int(4*S), anchor="ma")
        y += int(150*S)
    # divider line
    lw = int(120*S)
    d.line([(cx-lw, y+int(20*S)), (cx+lw, y+int(20*S))], fill=GOLD, width=max(1,int(2*S)))
    # subtitle
    fs = font(F_SANS, int(30*S))
    tracked(d, (cx, y+int(46*S)), sub.upper(), fs, DIM, tr=int(8*S), anchor="ma")
    im.save(path)

intro_png = os.path.join(tmp, "intro.png")
outro_png = os.path.join(tmp, "outro.png")
card(intro_png, "Interior Design Walkthrough", ["2 BHK", "RESIDENCE"],
     "A Complete Home Tour")
card(outro_png, "Thank You", ["THANK", "YOU"], "For Watching", big_font=F_THX)

# ---- per-room lower-third label (full-frame transparent PNG) ---------------
def label_png(path, idx, total_n, name):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    S = H / 1080.0
    # bottom scrim gradient (transparent -> dark) for legibility
    scrim_h = int(H*0.34)
    sc = Image.new("RGBA", (W, scrim_h), (0,0,0,0)); spx = sc.load()
    for y in range(scrim_h):
        a = int(150 * (y/scrim_h)**1.5)
        for x in range(W): spx[x, y] = (8, 8, 10, a)
    im.alpha_composite(sc, (0, H-scrim_h))
    x0 = int(W*0.07); yb = int(H*0.80)
    # index  e.g. 01 / 14
    fi = font(F_SANS, int(30*S))
    tracked(d, (x0, yb-int(60*S)), f"{idx:02d} / {total_n:02d}", fi, GOLD, tr=int(8*S))
    # room name (elegant serif)
    fn = font(F_DISP, int(92*S))
    d.text((x0-2, yb), name, font=fn, fill=(0,0,0,160))     # soft shadow
    d.text((x0, yb-2), name, font=fn, fill=CREAM+(255,))
    # accent underline
    namew = d.textlength(name, font=fn)
    uy = yb + int(108*S)
    d.line([(x0, uy), (x0+min(namew, W*0.5), uy)], fill=GOLD+(255,), width=max(1,int(3*S)))
    im.save(path)

# ---- helpers for eased Ken Burns moves -------------------------------------
def move_exprs(kind):
    Ts = f"(on/{Fden})"
    Sx = f"({Ts}*{Ts}*(3-2*{Ts}))"          # smoothstep ease
    c_x = "'iw/2-(iw/zoom/2)'"; c_y = "'ih/2-(ih/zoom/2)'"
    if kind == 0:   return f"z='1.0+0.14*{Sx}'", c_x, c_y
    if kind == 1:   return f"z='1.14-0.14*{Sx}'", c_x, c_y
    if kind == 2:   return "z='1.12'", f"x='(iw-iw/zoom)*{Sx}'", c_y
    if kind == 3:   return "z='1.12'", f"x='(iw-iw/zoom)*(1-{Sx})'", c_y
    if kind == 4:   return "z='1.12'", c_x, f"y='(ih-ih/zoom)*{Sx}'"
    return "z='1.12'", c_x, f"y='(ih-ih/zoom)*(1-{Sx})'"

GRADE = ("eq=contrast=1.07:saturation=1.12:brightness=0.012:gamma=0.97,"
         "colorbalance=rs=-0.04:bs=0.05:rm=0.02:bm=-0.02:rh=0.05:bh=-0.05,"
         "curves=master='0/0 0.25/0.21 0.5/0.52 0.78/0.82 1/1',"
         "vignette=PI/4.5,noise=alls=7:allf=t")

# ---- build room clips ------------------------------------------------------
clips = []   # (path, duration)
moves = [0, 2, 1, 3, 0, 4, 1, 2, 0, 3, 1, 5, 0, 2]
for idx, img in enumerate(imgs):
    base = os.path.splitext(os.path.basename(img))[0]
    name = NAMES.get(base, base.title())
    comp = os.path.join(tmp, f"c{idx:02d}.png")
    run(["-i", img, "-filter_complex",
         f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=increase,"
         f"crop={2*W}:{2*H},boxblur=55:6,eq=brightness=-0.05:saturation=1.05[bg];"
         f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=decrease[fg];"
         f"[bg][fg]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", comp])
    lbl = os.path.join(tmp, f"l{idx:02d}.png")
    label_png(lbl, idx+1, len(imgs), name)
    z, xe, ye = move_exprs(moves[idx % len(moves)])
    clip = os.path.join(tmp, f"clip{idx:02d}.mp4")
    fin = 0.5; fout = 0.5
    run(["-loop", "1", "-i", comp, "-loop", "1", "-i", lbl, "-t", str(DUR), "-r", str(FPS),
         "-filter_complex",
         f"[0:v]zoompan={z}:{xe}:{ye}:d={frames}:s={W}x{H}:fps={FPS},{GRADE},format=yuv420p[v];"
         f"[1:v]format=rgba,fade=t=in:st=0.3:d=0.6:alpha=1,"
         f"fade=t=out:st={DUR-0.6:.2f}:d=0.5:alpha=1[lb];"
         f"[v][lb]overlay=0:0:format=auto,"
         f"fade=t=in:st=0:d={fin},fade=t=out:st={DUR-fout:.2f}:d={fout}[out]",
         "-map", "[out]", "-c:v", "libx264", "-crf", "19", "-preset", "fast",
         "-pix_fmt", "yuv420p", clip])
    clips.append((clip, DUR))

# ---- intro/outro clips (subtle push-in + fades) ----------------------------
def card_clip(png, out, kind):
    z = "z='1.0+0.05*(on/%d)'" % int(CARD*FPS-1) if kind=="in" else "z='1.05-0.05*(on/%d)'" % int(CARD*FPS-1)
    run(["-loop","1","-i",png,"-t",str(CARD),"-r",str(FPS),"-filter_complex",
         f"[0:v]zoompan={z}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
         f"d={int(CARD*FPS)}:s={W}x{H}:fps={FPS},"
         f"fade=t=in:st=0:d=0.8,fade=t=out:st={CARD-0.8:.2f}:d=0.8,format=yuv420p[o]",
         "-map","[o]","-c:v","libx264","-crf","19","-preset","fast","-pix_fmt","yuv420p",out])
intro_clip = os.path.join(tmp, "intro.mp4"); outro_clip = os.path.join(tmp, "outro.mp4")
card_clip(intro_png, intro_clip, "in"); card_clip(outro_png, outro_clip, "out")

seq = [(intro_clip, CARD)] + clips + [(outro_clip, CARD)]

# ---- xfade chain -----------------------------------------------------------
TRANS = ["fade","smoothup","slideleft","fadeblack","wiperight","smoothright",
         "circleopen","slideup","fade","wipeleft","smoothleft","slidedown",
         "circleclose","fade","fade"]
inputs = []
for c,_ in seq: inputs += ["-i", c]
fc=[]; prev="0:v"; L=seq[0][1]; offsets=[]
for i in range(1, len(seq)):
    o = L - T; offsets.append(o)
    tr = TRANS[(i-1) % len(TRANS)]
    out = f"vx{i}"
    fc.append(f"[{prev}][{i}:v]xfade=transition={tr}:duration={T}:offset={o:.3f}[{out}]")
    prev = out; L = L + seq[i][1] - T
total = L
video_only = os.path.join(tmp, "video.mp4")
run([*inputs, "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
     "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-preset", "medium",
     "-pix_fmt", "yuv420p", video_only])

# ---- layered ambient music + whoosh SFX ------------------------------------
ambient = os.path.join(tmp, "amb.wav")
d = f"{total:.2f}"
run(["-filter_complex",
     f"sine=frequency=110:duration={d}[s0];"          # low root
     f"sine=frequency=220:duration={d}[s1];"
     f"sine=frequency=277.18:duration={d}[s2];"        # C#5 (A major-ish, warm)
     f"sine=frequency=329.63:duration={d}[s3];"
     f"sine=frequency=440:duration={d}[s4];"
     "[s0][s1][s2][s3][s4]amix=inputs=5:normalize=1,"
     "tremolo=f=0.14:d=0.5,"
     "aecho=0.8:0.88:70|220|400:0.5|0.32|0.18,"
     "lowpass=f=2000,highpass=f=70,volume=0.24,"
     f"afade=t=in:st=0:d=2,afade=t=out:st={total-2.5:.2f}:d=2.5[a]",
     "-map","[a]","-ar","44100","-t",d,ambient])
whoosh = os.path.join(tmp, "wh.wav")
run(["-filter_complex",
     "anoisesrc=color=brown:duration=0.6:amplitude=0.55,"
     "bandpass=f=850:width_type=h:w=1100,"
     "afade=t=in:st=0:d=0.15,afade=t=out:st=0.28:d=0.32,volume=0.45[w]",
     "-map","[w]","-ar","44100",whoosh])

ain = ["-i", video_only, "-i", ambient]
for _ in offsets: ain += ["-i", whoosh]
mix=[]; labels=["1:a"]
for k,o in enumerate(offsets):
    mix.append(f"[{2+k}:a]adelay={int(o*1000)}|{int(o*1000)}[w{k}]"); labels.append(f"w{k}")
mix.append("".join(f"[{l}]" for l in labels) +
           f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95[mix]")
run([*ain, "-filter_complex", ";".join(mix), "-map","0:v","-map","[mix]",
     "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",
     "-movflags","+faststart", OUT])
print(f"Done: {OUT}  ({total:.1f}s, {W}x{H}, {len(imgs)} rooms + intro/outro)")
