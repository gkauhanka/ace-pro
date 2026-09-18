#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fixtures
ffmpeg -hide_banner -loglevel error \
  -f lavfi -i 'color=c=0x123d30:s=640x360:r=24:d=12' \
  -f lavfi -i 'color=c=0xd7ee91:s=24x24:r=24:d=12' \
  -filter_complex "[0:v]drawbox=x=100:y=45:w=440:h=270:color=white@0.65:t=2,drawbox=x=145:y=45:w=350:h=270:color=white@0.65:t=2,drawbox=x=145:y=110:w=350:h=140:color=white@0.65:t=2,drawbox=x=319:y=110:w=2:h=140:color=white@0.65:t=fill,drawbox=x=80:y=179:w=480:h=2:color=white@0.9:t=fill[bg];[1:v]format=rgba,geq=r=215:g=238:b=145:a='if(lte(pow(X-12,2)+pow(Y-12,2),100),255,0)'[ball];[bg][ball]overlay=x='308+140*sin(t*1.8)':y='168+95*cos(t*2.2)':shortest=1,format=yuv420p[out]" \
  -map '[out]' -c:v libx264 -movflags +faststart -y fixtures/court-demo.mp4
