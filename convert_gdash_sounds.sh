#!/bin/sh

# This script downloads the sampled sound files from GDash and converts
# them to a smaller version (half sample rate), and copies those
# into the sounds folder inside our package. Format: Ogg
# Usually you don't have to run this script because the converted
# sample files are included in the bouldercaves repository already.
# GDash is here:  https://bitbucket.org/czirkoszoltan/gdash.git

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
FFMPEG_OPTS="-v error -hide_banner -ar 22050 -ac 1 -y"
OEXT="ogg"

ffmpeg -i ${GDASH}../music/bd1.ogg ${FFMPEG_OPTS} ${OUT}bdmusic.${OEXT}
ffmpeg -i ${GDASH}bonus_life.ogg ${FFMPEG_OPTS} ${OUT}bonus_life.${OEXT}
ffmpeg -i ${GDASH}stone.ogg ${FFMPEG_OPTS} ${OUT}boulder.${OEXT}
ffmpeg -i ${GDASH}diamond_collect.ogg ${FFMPEG_OPTS} ${OUT}collectdiamond.${OEXT}
ffmpeg -i ${GDASH}cover.ogg ${FFMPEG_OPTS} ${OUT}cover.${OEXT}
ffmpeg -i ${GDASH}crack.ogg ${FFMPEG_OPTS} ${OUT}crack.${OEXT}
ffmpeg -i ${GDASH}slime.ogg ${FFMPEG_OPTS} ${OUT}slime.${OEXT}
ffmpeg -i ${GDASH}explosion.ogg ${FFMPEG_OPTS} ${OUT}explosion.${OEXT}
ffmpeg -i ${GDASH}voodoo_explosion.ogg ${FFMPEG_OPTS} ${OUT}voodoo_explosion.${OEXT}
ffmpeg -i ${GDASH}finished.ogg ${FFMPEG_OPTS} ${OUT}finished.${OEXT}
ffmpeg -i ${GDASH}walk_empty.ogg ${FFMPEG_OPTS} ${OUT}walk_empty.${OEXT}
ffmpeg -i ${GDASH}walk_earth.ogg ${FFMPEG_OPTS} ${OUT}walk_dirt.${OEXT}
ffmpeg -i ${GDASH}diamond_1.ogg ${FFMPEG_OPTS} ${OUT}diamond1.${OEXT}
ffmpeg -i ${GDASH}diamond_2.ogg ${FFMPEG_OPTS} ${OUT}diamond2.${OEXT}
ffmpeg -i ${GDASH}diamond_3.ogg ${FFMPEG_OPTS} ${OUT}diamond3.${OEXT}
ffmpeg -i ${GDASH}diamond_4.ogg ${FFMPEG_OPTS} ${OUT}diamond4.${OEXT}
ffmpeg -i ${GDASH}diamond_5.ogg ${FFMPEG_OPTS} ${OUT}diamond5.${OEXT}
ffmpeg -i ${GDASH}diamond_6.ogg ${FFMPEG_OPTS} ${OUT}diamond6.${OEXT}
ffmpeg -i ${GDASH}timeout_1.ogg ${FFMPEG_OPTS} ${OUT}timeout1.${OEXT}
ffmpeg -i ${GDASH}timeout_2.ogg ${FFMPEG_OPTS} ${OUT}timeout2.${OEXT}
ffmpeg -i ${GDASH}timeout_3.ogg ${FFMPEG_OPTS} ${OUT}timeout3.${OEXT}
ffmpeg -i ${GDASH}timeout_4.ogg ${FFMPEG_OPTS} ${OUT}timeout4.${OEXT}
ffmpeg -i ${GDASH}timeout_5.ogg ${FFMPEG_OPTS} ${OUT}timeout5.${OEXT}
ffmpeg -i ${GDASH}timeout_6.ogg ${FFMPEG_OPTS} ${OUT}timeout6.${OEXT}
ffmpeg -i ${GDASH}timeout_7.ogg ${FFMPEG_OPTS} ${OUT}timeout7.${OEXT}
ffmpeg -i ${GDASH}timeout_8.ogg ${FFMPEG_OPTS} ${OUT}timeout8.${OEXT}
ffmpeg -i ${GDASH}timeout_9.ogg ${FFMPEG_OPTS} ${OUT}timeout9.${OEXT}
ffmpeg -i ${GDASH}timeout.ogg ${FFMPEG_OPTS} ${OUT}game_over.${OEXT}
ffmpeg -i ${GDASH}amoeba.ogg ${FFMPEG_OPTS} ${OUT}amoeba.${OEXT}
ffmpeg -i ${GDASH}magic_wall.ogg ${FFMPEG_OPTS} ${OUT}magic_wall.${OEXT}
ffmpeg -i ${GDASH}box_push.ogg ${FFMPEG_OPTS} ${OUT}box_push.${OEXT}

echo "Done!"
