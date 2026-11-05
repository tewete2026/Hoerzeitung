#!/bin/bash
echo  "----------Reorg Order Chapter:START"

doReplace () {
    mv -v ${1} ${1}.bck
    mv -v ${2} ${1}
    mv -v ${1}.bck ${2}
}

cd ${1}/
doReplace 1074/1074-06.mp3 1074/1074-07.mp3

echo  "----------Reorg Order Chapter:ENDE"
