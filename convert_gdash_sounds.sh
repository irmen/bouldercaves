#!/bin/sh

GDASH_ROOT="./_gdash"
GDASH="${GDASH_ROOT}/sound/"
OUT="./bouldercaves/sounds/"
SFORMAT="pcm_s16le"   # pcm_s16le

CURDIR=$(pwd)
mkdir ${GDASH_ROOT}
cd ${GDASH_ROOT}
git init
git remote add -f origin https://bitbucket.org/czirkoszoltan/gdash.git
git config core.sparseCheckout true
echo "music/" >> .git/info/sparse-checkout
echo "sound/" >> .git/info/sparse-checkout
git pull --depth 1 origin master
# git clone --depth 1 https://bitbucket.org/czirkoszoltan/gdash.git ${GDASH_ROOT}

cd ${CURDIR}

ffmpeg -i ${GDASH}../music/bd1.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}bdmusic.wav
ffmpeg -i ${GDASH}bonus_life.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}bonus_life.wav
ffmpeg -i ${GDASH}stone.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}boulder.wav
ffmpeg -i ${GDASH}diamond_collect.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}collectdiamond.wav
ffmpeg -i ${GDASH}cover.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}cover.wav
ffmpeg -i ${GDASH}crack.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}crack.wav
ffmpeg -i ${GDASH}explosion.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}explosion.wav
ffmpeg -i ${GDASH}finished.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}finished.wav
ffmpeg -i ${GDASH}walk_empty.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}walk_empty.wav
ffmpeg -i ${GDASH}walk_earth.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}walk_dirt.wav

ffmpeg -i ${GDASH}diamond_1.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond1.wav
ffmpeg -i ${GDASH}diamond_2.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond2.wav
ffmpeg -i ${GDASH}diamond_3.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond3.wav
ffmpeg -i ${GDASH}diamond_4.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond4.wav
ffmpeg -i ${GDASH}diamond_5.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond5.wav
ffmpeg -i ${GDASH}diamond_6.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}diamond6.wav

ffmpeg -i ${GDASH}timeout_1.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout1.wav
ffmpeg -i ${GDASH}timeout_2.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout2.wav
ffmpeg -i ${GDASH}timeout_3.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout3.wav
ffmpeg -i ${GDASH}timeout_4.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout4.wav
ffmpeg -i ${GDASH}timeout_5.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout5.wav
ffmpeg -i ${GDASH}timeout_6.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout6.wav
ffmpeg -i ${GDASH}timeout_7.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout7.wav
ffmpeg -i ${GDASH}timeout_8.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout8.wav
ffmpeg -i ${GDASH}timeout_9.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout9.wav
ffmpeg -i ${GDASH}timeout.ogg -hide_banner -ar 22100 -ac 1 -f wav -acodec ${SFORMAT} -y ${OUT}timeout.wav
