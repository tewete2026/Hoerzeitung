import os, random
from math import floor
from flask import current_app
from mutagen.mp3 import MP3
from mutagen.id3 import CHAP
from sox import file_info as audio_info


def getMP3Info(rawname:str):
    ts = current_app.config["TS"]
    # audio = MP3(current_app.instance_path + "/" + mp3, ID3=EasyID3)
    audio = MP3(rawname)
    episode_kap = {}
    description = "- - - -"
    title = "---"
    tlen = None
    for key in audio.keys():
        cont = audio.get(key)
        if isinstance(cont, CHAP):
            text = cont.sub_frames["TIT2"][0]
            if len(text) > 0:
                episode_kap.update({key.removeprefix("CHAP:"):text})
        if key == 'TIT2':
            title = str(cont)
        if key == 'TLEN':
            tlen = str(cont)
        if key[:5] == 'COMM:':
            description = str(cont)
    # keys = ["TALB", "TPE1", "TDRC", "TIT2", "TENC", "TLEN"]
    # for key in keys:
    #     print(key, audio.get(key))
    size = os.stat(rawname).st_size
    chapter = ""
    counter = 1
    for key, text in episode_kap.items():
        chapter += "{0:02}. {1}<br>".format(counter, text)
        counter += 1
    published = ts.fromtimestamp(os.stat(rawname).st_mtime)
    if tlen is None:
        dur = audio.info.length
    else:
        dur = float(tlen[0]) / 1000
    min = dur / 60
    sec = dur % 60
    duration = "{0:02.0f}:{1:02.0f}".format(min, sec)
    # print(tlen, dur, min, sec, duration, audio, audio.keys())
    return (title, description, published, size, duration, chapter)


def getMpegInfo(rawname:str):
    sec = audio_info.duration(rawname)
    if sec is None: dur = 0.00
    else: dur = sec
    duration = "{0:02.0f}:{1:02.0f}".format(floor(dur / 60), floor(dur % 60))
    size = os.stat(rawname).st_size
    return (size, duration)


def generateCode(prefix:str):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    chars_list = list(chars)
    code = ''
    for z in range(1, 5):
        code += "".join(random.sample(chars_list, 4))
        if z < 4: code += '-'
    return str(prefix) + code
