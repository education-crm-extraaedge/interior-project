#!/usr/bin/env bash
# Ken Burns slow zoom-in video from a still image.
# Usage: ./make_video.sh [input_image] [output.mp4] [duration_seconds]
set -euo pipefail

IN="${1:-}"
OUT="${2:-room_video.mp4}"
DUR="${3:-10}"          # seconds
FPS=30
W=1920; H=1080          # output resolution

# Auto-pick first image if none given
if [[ -z "$IN" ]]; then
  IN=$(find . -maxdepth 2 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) \
        ! -path './.git/*' | head -n1 || true)
fi
[[ -z "$IN" || ! -f "$IN" ]] && { echo "No input image found. Pass one as arg 1."; exit 1; }

# ffmpeg: use bundled static binary from imageio-ffmpeg if system ffmpeg is absent
FF=$(command -v ffmpeg || python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")

FRAMES=$(( DUR * FPS ))
# Upscale source first so zoompan motion is smooth (avoids pixel jitter),
# slow zoom from 1.0x to ~1.25x, kept centered.
"$FF" -y -loop 1 -i "$IN" -filter_complex \
"scale=-2:2160:flags=lanczos,\
zoompan=z='min(zoom+0.0006,1.25)':d=${FRAMES}:\
x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS}" \
  -c:v libx264 -t "$DUR" -r "$FPS" -pix_fmt yuv420p -movflags +faststart "$OUT"

echo "Created: $OUT"
