SED=`which sed`
FILENAME=description.xml
findverline=`cat src/${FILENAME} | grep "<version value=" -n | cut -d: -f1`
linenum=${findverline}
version=`cat version`

#${SED} -i "${linenum}d" src/${FILENAME}
${SED} -i ${linenum}c\ "    <version value=\"${version}\"/>" src/${FILENAME}
${SED} -i "${linenum}s/^/\t/" src/${FILENAME}
