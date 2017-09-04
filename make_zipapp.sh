#!/bin/sh
OUTFILE="bouldercaves.pyz"
TMPFILE="@bouldercaves.zip"

echo
echo Creating self-contained executable Python zip file application.
echo

find . -name '*.pyc' -exec rm {} \;
find . -name __pycache__ -exec rm -r {} \;
rm -f ${TMPFILE} ${OUTPUTFILE}
cat <<EOT >> __main__.py
import sys
from bouldercaves import gfxwindow

gfxwindow.start(sys.argv[1:])
EOT
7z a -mx=9 ${TMPFILE} bouldercaves __main__.py
rm __main__.py
echo "#!/usr/bin/env python3" > ${OUTFILE}
cat ${TMPFILE} >> ${OUTFILE}
chmod u+x ${OUTFILE}
rm ${TMPFILE}

echo
echo Done, output is ${OUTFILE}
echo
