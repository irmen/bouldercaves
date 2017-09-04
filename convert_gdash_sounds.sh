#!/bin/sh

GDASH_ROOT="./_gdash"
GDASH="${GDASH_ROOT}/sound/"
OUT="./bouldercaves/sounds/"

if [ ! -e "${GDASH}stone.ogg" ]; then
    # checkout the sound files from GDash
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
else
    echo "Sound files from GDash already exist."
fi

echo "Converting source sound files..."
FFMPEG_OPTS="-v error -hide_banner -ar 22100 -ac 1 -f wav -acodec pcm_s16le -y"

ffmpeg -i ${GDASH}../music/bd1.ogg ${FFMPEG_OPTS} ${OUT}bdmusic.wav
ffmpeg -i ${GDASH}bonus_life.ogg ${FFMPEG_OPTS} ${OUT}bonus_life.wav
ffmpeg -i ${GDASH}stone.ogg ${FFMPEG_OPTS} ${OUT}boulder.wav
ffmpeg -i ${GDASH}diamond_collect.ogg ${FFMPEG_OPTS} ${OUT}collectdiamond.wav
ffmpeg -i ${GDASH}cover.ogg ${FFMPEG_OPTS} ${OUT}cover.wav
ffmpeg -i ${GDASH}crack.ogg ${FFMPEG_OPTS} ${OUT}crack.wav
ffmpeg -i ${GDASH}explosion.ogg ${FFMPEG_OPTS} ${OUT}explosion.wav
ffmpeg -i ${GDASH}finished.ogg ${FFMPEG_OPTS} ${OUT}finished.wav
ffmpeg -i ${GDASH}walk_empty.ogg ${FFMPEG_OPTS} ${OUT}walk_empty.wav
ffmpeg -i ${GDASH}walk_earth.ogg ${FFMPEG_OPTS} ${OUT}walk_dirt.wav
ffmpeg -i ${GDASH}diamond_1.ogg ${FFMPEG_OPTS} ${OUT}diamond1.wav
ffmpeg -i ${GDASH}diamond_2.ogg ${FFMPEG_OPTS} ${OUT}diamond2.wav
ffmpeg -i ${GDASH}diamond_3.ogg ${FFMPEG_OPTS} ${OUT}diamond3.wav
ffmpeg -i ${GDASH}diamond_4.ogg ${FFMPEG_OPTS} ${OUT}diamond4.wav
ffmpeg -i ${GDASH}diamond_5.ogg ${FFMPEG_OPTS} ${OUT}diamond5.wav
ffmpeg -i ${GDASH}diamond_6.ogg ${FFMPEG_OPTS} ${OUT}diamond6.wav
ffmpeg -i ${GDASH}timeout_1.ogg ${FFMPEG_OPTS} ${OUT}timeout1.wav
ffmpeg -i ${GDASH}timeout_2.ogg ${FFMPEG_OPTS} ${OUT}timeout2.wav
ffmpeg -i ${GDASH}timeout_3.ogg ${FFMPEG_OPTS} ${OUT}timeout3.wav
ffmpeg -i ${GDASH}timeout_4.ogg ${FFMPEG_OPTS} ${OUT}timeout4.wav
ffmpeg -i ${GDASH}timeout_5.ogg ${FFMPEG_OPTS} ${OUT}timeout5.wav
ffmpeg -i ${GDASH}timeout_6.ogg ${FFMPEG_OPTS} ${OUT}timeout6.wav
ffmpeg -i ${GDASH}timeout_7.ogg ${FFMPEG_OPTS} ${OUT}timeout7.wav
ffmpeg -i ${GDASH}timeout_8.ogg ${FFMPEG_OPTS} ${OUT}timeout8.wav
ffmpeg -i ${GDASH}timeout_9.ogg ${FFMPEG_OPTS} ${OUT}timeout9.wav
ffmpeg -i ${GDASH}timeout.ogg ${FFMPEG_OPTS} ${OUT}game_over.wav
ffmpeg -i ${GDASH}amoeba.ogg ${FFMPEG_OPTS} ${OUT}amoeba.wav
ffmpeg -i ${GDASH}magic_wall.ogg ${FFMPEG_OPTS} ${OUT}magic_wall.wav
ffmpeg -i ${GDASH}box_push.ogg ${FFMPEG_OPTS} ${OUT}box_push.wav

echo "Done!"
