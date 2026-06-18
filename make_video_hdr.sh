#!/usr/bin/env bash
# Ken Burns slow zoom-in video, encoded as HDR10 (HEVC Main10, BT.2020, PQ).
#
# NOTE: The source is an 8-bit SDR image, so this is an HDR10-*flagged*/container
# output (10-bit, BT.2020 primaries, SMPTE-2084 PQ transfer, HDR10 metadata).
# It plays in HDR mode on HDR displays, but real captured dynamic range is
# limited by the SDR source — it is not a true HDR-graded master.
#
# Usage: ./make_video_hdr.sh [input_image] [output.mp4] [duration_seconds]
set -euo pipefail

IN="${1:-}"
OUT="${2:-room_video_hdr.mp4}"
DUR="${3:-10}"
FPS=30
W=1920; H=1080

if [[ -z "$IN" ]]; then
  IN=$(find . -maxdepth 2 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) \
        ! -path './.git/*' | head -n1 || true)
fi
[[ -z "$IN" || ! -f "$IN" ]] && { echo "No input image found. Pass one as arg 1."; exit 1; }

FF=$(command -v ffmpeg || python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
FRAMES=$(( DUR * FPS ))

"$FF" -y -loop 1 -i "$IN" -t "$DUR" -r "$FPS" -filter_complex \
"scale=-2:2160:flags=lanczos,\
zoompan=z='min(zoom+0.0006,1.25)':d=${FRAMES}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},\
format=yuv444p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,\
zscale=tin=bt709:min=bt709:pin=bt709:rin=tv:t=linear:npl=100,format=gbrpf32le,\
zscale=p=bt2020,zscale=t=smpte2084:m=bt2020nc:r=tv,format=yuv420p10le" \
  -c:v libx265 -pix_fmt yuv420p10le \
  -x265-params "colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1):max-cll=1000,400:hdr-opt=1:repeat-headers=1" \
  -color_primaries bt2020 -color_trc smpte2084 -colorspace bt2020nc \
  -tag:v hvc1 -movflags +faststart "$OUT"

echo "Created HDR10 video: $OUT"
