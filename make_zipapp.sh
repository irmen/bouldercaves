#!/bin/sh
OUTFILE="bouldercaves.pyz"
OUTFILESYNTH="bouldercaves-synth.pyz"
TMPFILE="@bouldercaves.zip"

echo
echo Creating self-contained executable Python zip file applications
echo ---------------------------------------------------------------
echo

find . -name '*.pyc' -exec rm {} \;
find . -name __pycache__ -exec rm -r {} \;
rm -f ${TMPFILE} *.pyz

# create the zipapp including the sound files
echo with samples...
cat <<EOT > __main__.py
import sys
from bouldercaves import game

game.start(sys.argv[1:])
EOT

7z a -bd -bso0 -tzip -mx=9 ${TMPFILE} bouldercaves __main__.py
echo "#!/usr/bin/env python3" > ${OUTFILE}
cat ${TMPFILE} >> ${OUTFILE}
chmod u+x ${OUTFILE}
rm ${TMPFILE}

# create the zipapp without any sound files, relying on the synth alone
echo without samples...
cat <<EOT > __main__.py
import sys
from bouldercaves import game

game.start(["--synth"] + sys.argv[1:])
EOT

7z a -bd -bso0 -tzip -mx=9 ${TMPFILE} '-xr!bouldercaves/sounds/*' bouldercaves __main__.py
echo "#!/usr/bin/env python3" > ${OUTFILESYNTH}
cat ${TMPFILE} >> ${OUTFILESYNTH}
chmod u+x ${OUTFILESYNTH}
rm ${TMPFILE}

rm __main__.py

echo
echo Done, output files are:
echo -----------------------
ls -shk -c1 *.pyz
echo
