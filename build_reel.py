#!/usr/bin/env python3
"""Build a 9:16 Instagram reel from all room images: blurred-bg + Ken Burns
zoom per room, varied transitions, and generated ambient music + whoosh SFX."""
import os, subprocess, glob, sys, math, tempfile

import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

W, H = 1080, 1920
FPS = 30
DUR = 3.0          # seconds shown per room (before transition overlap)
T   = 0.8          # transition duration (seconds)
OUT = sys.argv[1] if len(sys.argv) > 1 else "interior_reel.mp4"

# ---- curated room order (nice walkthrough); leftovers appended -------------
PREFERRED = [
    "entrance area", "wall pannaling and livingarea", "Hall", "ROOM",
    "studytablenadtvunit", "L-kitechen", "diningare", "dinner area",
    "3rd view dinner area", "2ndbedroom", "bed-frount", "bedroom-wardrobe",
    "2nd wardrobe", "2nd study table",
]
imgs = [f for f in glob.glob("*.jp*g") + glob.glob("*.png") + glob.glob("*.webp")]
def rank(f):
    base = os.path.splitext(os.path.basename(f))[0]
    return PREFERRED.index(base) if base in PREFERRED else len(PREFERRED)
imgs = sorted(imgs, key=lambda f: (rank(f), f.lower()))
if not imgs:
    sys.exit("No images found.")
print("Order:", *(os.path.basename(i) for i in imgs), sep="\n  ")

tmp = tempfile.mkdtemp(prefix="reel_")
frames = int(DUR * FPS)

def run(cmd):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *cmd])
    if r.returncode: sys.exit("ffmpeg failed: " + " ".join(map(str, cmd[:6])) + " ...")

# ---- 1. per-room clip: blurred fill bg + fitted sharp fg + Ken Burns zoom ---
clips = []
for idx, img in enumerate(imgs):
    comp = os.path.join(tmp, f"comp_{idx:02d}.png")
    run(["-i", img, "-filter_complex",
         f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=increase,"
         f"crop={2*W}:{2*H},boxblur=60:8,eq=brightness=-0.06:saturation=1.08[bg];"
         f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=decrease[fg];"
         f"[bg][fg]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", comp])
    clip = os.path.join(tmp, f"clip_{idx:02d}.mp4")
    zin  = (idx % 2 == 0)   # alternate zoom-in / zoom-out for variety
    if zin:
        z = "z='min(zoom+0.0006,1.18)'"
    else:
        z = "z='if(eq(on,0),1.18,max(zoom-0.0006,1.0))'"
    run(["-loop", "1", "-i", comp, "-t", str(DUR), "-r", str(FPS), "-vf",
         f"zoompan={z}:d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
         f"s={W}x{H}:fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", clip])
    clips.append(clip)

# ---- 2. xfade chain with varied transitions --------------------------------
TRANS = ["fade", "slideleft", "wiperight", "smoothup", "circleopen",
         "slideup", "fadeblack", "wipeleft", "smoothright", "circleclose",
         "slidedown", "diagtl", "fade"]
inputs = []
for c in clips: inputs += ["-i", c]
fc, prev, offset, offsets = [], "0:v", 0.0, []
for i in range(1, len(clips)):
    offset += DUR - T
    offsets.append(offset)
    tr = TRANS[(i - 1) % len(TRANS)]
    out = f"vx{i}"
    fc.append(f"[{prev}][{i}:v]xfade=transition={tr}:duration={T}:"
              f"offset={offset:.3f}[{out}]")
    prev = out
total = len(clips) * DUR - (len(clips) - 1) * T
fc.append(f"[{prev}]fade=t=in:st=0:d=0.6,fade=t=out:st={total-0.8:.3f}:d=0.8[vout]")
video_only = os.path.join(tmp, "video_only.mp4")
run([*inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
     "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-preset", "medium",
     "-pix_fmt", "yuv420p", video_only])

# ---- 3. ambient music bed (A-minor chord pad + tremolo + reverb) -----------
ambient = os.path.join(tmp, "ambient.wav")
chord = ("sine=frequency=220:duration={d}[a];"
         "sine=frequency=261.63:duration={d}[b];"
         "sine=frequency=329.63:duration={d}[c];"
         "sine=frequency=440:duration={d}[e];").format(d=f"{total:.2f}")
run(["-filter_complex",
     chord +
     "[a][b][c][e]amix=inputs=4:normalize=1,"
     "tremolo=f=0.18:d=0.6,"                       # slow swell
     "aecho=0.8:0.85:60|180|350:0.5|0.35|0.2,"     # spacious reverb-ish
     "lowpass=f=1800,highpass=f=80,"
     "volume=0.22,"
     f"afade=t=in:st=0:d=1.5,afade=t=out:st={total-2:.2f}:d=2[aout]",
     "-map", "[aout]", "-ar", "44100", "-t", f"{total:.2f}", ambient])

# ---- 4. whoosh SFX (filtered noise sweep) ----------------------------------
whoosh = os.path.join(tmp, "whoosh.wav")
run(["-filter_complex",
     "anoisesrc=color=brown:duration=0.6:amplitude=0.6,"
     "bandpass=f=900:width_type=h:w=1200,"
     "afade=t=in:st=0:d=0.15,afade=t=out:st=0.3:d=0.3,volume=0.5[w]",
     "-map", "[w]", "-ar", "44100", whoosh])

# ---- 5. final mux: video + ambient + whooshes at each transition -----------
ain = ["-i", video_only, "-i", ambient]
for _ in offsets: ain += ["-i", whoosh]
mix = []
amix_labels = ["1:a"]
for k, off in enumerate(offsets):
    lbl = f"wd{k}"
    mix.append(f"[{2+k}:a]adelay={int(off*1000)}|{int(off*1000)}[{lbl}]")
    amix_labels.append(lbl)
mix.append("".join(f"[{l}]" for l in amix_labels) +
           f"amix=inputs={len(amix_labels)}:normalize=0,"
           f"alimiter=limit=0.95[mix]")
run([*ain, "-filter_complex", ";".join(mix),
     "-map", "0:v", "-map", "[mix]",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
     "-movflags", "+faststart", OUT])

print(f"\nDone: {OUT}  ({total:.1f}s, {W}x{H}, {len(clips)} rooms)")
