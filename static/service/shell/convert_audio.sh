#!/bin/bash
/usr/bin/ffmpeg -hide_banner -i ${1} -vn -c:a libmp3lame -q:a 5 -y ${2}
