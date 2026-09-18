#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../../docs/media
ffmpeg -hide_banner -loglevel error -i raw/walkthrough.webm \
  -an -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart \
  -y ../../docs/media/ace-pro-walkthrough.mp4
ffmpeg -hide_banner -loglevel error -i raw/walkthrough.webm \
  -filter_complex 'fps=8,scale=320:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle' \
  -loop 0 -y ../../docs/media/ace-pro-preview.gif
